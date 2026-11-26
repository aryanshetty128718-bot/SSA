import threading
import time
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal
from app.models.product import Product
from app.services.analysis_service import analysis_service
from app.core.logging_config import logger

class RescoringJobManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.job_status = {
                    "job_id": None,
                    "status": "idle",  # idle, running, completed, failed
                    "progress_pct": 0.0,
                    "processed_count": 0,
                    "total_count": 0,
                    "target_version": None,
                    "started_at": None,
                    "completed_at": None,
                    "error": None
                }
            return cls._instance

    def get_status(self) -> Dict[str, Any]:
        return self.job_status.copy()

    def start_rescoring(self, target_version: str = "1.2.0", description: str = "") -> Dict[str, Any]:
        with self._lock:
            if self.job_status["status"] == "running":
                return {"message": "A re-scoring job is already running", "status": self.job_status}

            job_id = f"rescore_{int(time.time())}"
            self.job_status = {
                "job_id": job_id,
                "status": "running",
                "progress_pct": 0.0,
                "processed_count": 0,
                "total_count": 0,
                "target_version": target_version,
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "error": None
            }

            thread = threading.Thread(
                target=self._run_rescoring,
                args=(job_id, target_version, description),
                daemon=True
            )
            thread.start()

            return {
                "message": f"Background re-scoring job {job_id} initiated",
                "target_version": target_version,
                "status_endpoint": "/api/v1/admin/rescore/status"
            }

    def _run_rescoring(self, job_id: str, target_version: str, description: str):
        logger.info(f"Background re-scoring job {job_id} started for version {target_version}")
        db: Session = SessionLocal()
        try:
            # 1. Update version history table
            db.execute(text("UPDATE scoring_version_history SET is_active = 0"))
            db.execute(text("""
                INSERT INTO scoring_version_history (version, released_at, description, is_active)
                VALUES (:version, CURRENT_TIMESTAMP, :desc, 1)
            """), {"version": target_version, "desc": description or f"Administrative update to scoring criteria (v{target_version})"})
            db.commit()

            # 2. Rescore catalog products
            products = db.query(Product).all()
            total = len(products)
            self.job_status["total_count"] = total

            for i, prod in enumerate(products, start=1):
                try:
                    analysis = analysis_service.analyze_product(prod, db)
                    # Ensure score row holds the new target_version
                    if prod.product_score:
                        prod.product_score.scoring_engine_version = target_version
                        db.commit()
                except Exception as e:
                    logger.warning(f"Error re-scoring product {prod.id}: {e}")
                    db.rollback()

                self.job_status["processed_count"] = i
                self.job_status["progress_pct"] = round((i / total) * 100.0, 1) if total > 0 else 100.0

            self.job_status["status"] = "completed"
            self.job_status["completed_at"] = datetime.utcnow().isoformat()
            logger.info(f"Background re-scoring job {job_id} completed successfully for {total} products")
        except Exception as exc:
            logger.exception(f"Background re-scoring job {job_id} failed: {exc}")
            self.job_status["status"] = "failed"
            self.job_status["error"] = str(exc)
        finally:
            db.close()

rescoring_manager = RescoringJobManager()
