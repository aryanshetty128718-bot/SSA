const puppeteer = require('../frontend/node_modules/puppeteer');
const fs = require('fs');
const path = require('path');
const http = require('http');

const SCREENSHOT_DIR = path.resolve(__dirname, '../docs/screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function getAdminToken() {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({ email: 'admin@example.com', password: 'Admin@12345' });
    const req = http.request(
      {
        hostname: '127.0.0.1',
        port: 8000,
        path: '/api/v1/auth/login',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData),
        },
      },
      (res) => {
        let body = '';
        res.on('data', (chunk) => (body += chunk));
        res.on('end', () => {
          try {
            const data = JSON.parse(body);
            resolve(data);
          } catch (e) {
            reject(e);
          }
        });
      }
    );
    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

async function capture() {
  console.log('Fetching Admin JWT token directly from API...');
  const authData = await getAdminToken();
  console.log('Logged in as:', authData.user?.email, 'Role:', authData.user?.role);

  console.log('Launching Puppeteer browser...');
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });

  const page = await browser.newPage();
  const BASE_URL = 'http://localhost:5173';

  // Helper to set viewport and wait
  const setViewport = async (w, h) => {
    await page.setViewport({ width: w, height: h });
  };

  // 1. Home
  console.log('Capturing Home (Desktop & Mobile)...');
  await setViewport(1280, 800);
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 600));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'home_desktop.png'), fullPage: true });

  await setViewport(390, 844);
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 600));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'home_mobile.png'), fullPage: true });

  // 2. Nutella Analysis
  console.log('Capturing Nutella Analysis (Desktop, Tabs, Mobile)...');
  await setViewport(1280, 800);
  await page.goto(`${BASE_URL}/products/3017620422003`, { waitUntil: 'networkidle2' });
  await page.waitForSelector('h1', { timeout: 10000 }).catch(() => {});
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'nutella_desktop.png'), fullPage: true });

  // Click Nutrition tab
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const b = btns.find(el => el.textContent && el.textContent.includes('Nutrition Facts'));
    if (b) b.click();
  });
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'nutella_nutrition_fixed.png'), fullPage: true });

  // Click Ingredients tab
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const b = btns.find(el => el.textContent && el.textContent.includes('Ingredients & Additives'));
    if (b) b.click();
  });
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'nutella_ingredients_fixed.png'), fullPage: true });

  // Nutella Mobile
  await setViewport(390, 844);
  await page.goto(`${BASE_URL}/products/3017620422003`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'nutella_mobile.png'), fullPage: true });

  // 3. Low-Data Product Analysis (0012700158042 Skinner Spaghetti)
  console.log('Capturing Low-Data Product Analysis (Desktop & Mobile)...');
  await setViewport(1280, 800);
  await page.goto(`${BASE_URL}/products/0012700158042`, { waitUntil: 'networkidle2' });
  await page.waitForSelector('h1', { timeout: 10000 }).catch(() => {});
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'low_data_desktop.png'), fullPage: true });

  await setViewport(390, 844);
  await page.goto(`${BASE_URL}/products/0012700158042`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'low_data_mobile.png'), fullPage: true });

  // 4. Alternatives (Nutella Alternatives)
  console.log('Capturing Alternatives (Desktop & Mobile)...');
  await setViewport(1280, 800);
  await page.goto(`${BASE_URL}/alternatives/3017620422003`, { waitUntil: 'networkidle2' });
  await page.waitForSelector('h1, h2', { timeout: 10000 }).catch(() => {});
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'alternatives_desktop.png'), fullPage: true });
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'nutella_alternatives_fixed.png'), fullPage: true });

  await setViewport(390, 844);
  await page.goto(`${BASE_URL}/alternatives/3017620422003`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'alternatives_mobile.png'), fullPage: true });

  // 5. Compare 3 Products (Nutella, Coca-Cola, Marie Gold)
  console.log('Capturing Compare 3 Products (Desktop & Mobile)...');
  await setViewport(1280, 800);
  await page.goto(`${BASE_URL}/compare?ids=3017620422003,5449000000439,8901063023901`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'compare_desktop.png'), fullPage: true });

  await setViewport(390, 844);
  await page.goto(`${BASE_URL}/compare?ids=3017620422003,5449000000439,8901063023901`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'compare_mobile.png'), fullPage: true });

  // 6. Login
  console.log('Capturing Login (Desktop & Mobile)...');
  await setViewport(1280, 800);
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 600));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'login_desktop.png') });

  await setViewport(390, 844);
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 600));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'login_mobile.png') });

  // 7. Inject Auth into Browser LocalStorage for Admin & User Dashboard
  console.log('Injecting authenticated session into browser...');
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle2' });
  await page.evaluate((token) => {
    localStorage.setItem('ssa_auth_token', token);
    localStorage.setItem('ssa_auth_user', JSON.stringify({
      id: "admin-id",
      email: "admin@example.com",
      role: "admin",
      full_name: "System Administrator"
    }));
  }, authData.access_token);

  // 8. User Dashboard
  console.log('Capturing User Dashboard (Desktop & Mobile)...');
  await setViewport(1280, 800);
  await page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'user_dashboard_desktop.png'), fullPage: true });

  await setViewport(390, 844);
  await page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'user_dashboard_mobile.png'), fullPage: true });

  // 9. Admin Dashboard (Analytics tab)
  console.log('Capturing Admin Dashboard (Desktop & Mobile)...');
  await setViewport(1280, 800);
  await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'admin_desktop.png'), fullPage: true });

  await setViewport(390, 844);
  await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'admin_mobile.png'), fullPage: true });

  // 10. Admin Criteria Editor tab
  console.log('Capturing Admin Criteria Editor (Desktop & Mobile)...');
  await setViewport(1280, 800);
  await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1000));
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const criteriaBtn = btns.find(b => b.textContent && b.textContent.includes('Scoring Engine Config'));
    if (criteriaBtn) criteriaBtn.click();
  });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'admin_criteria_desktop.png'), fullPage: true });

  await setViewport(390, 844);
  await page.goto(`${BASE_URL}/admin`, { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1000));
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const criteriaBtn = btns.find(b => b.textContent && b.textContent.includes('Scoring Engine Config'));
    if (criteriaBtn) criteriaBtn.click();
  });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'admin_criteria_mobile.png'), fullPage: true });

  await browser.close();
  console.log('All desktop and mobile screenshots captured successfully!');
}

capture().catch((err) => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});
