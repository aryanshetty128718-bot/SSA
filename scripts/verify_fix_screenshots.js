const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = path.resolve(__dirname, '../docs/screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function verify() {
  console.log('Launching Puppeteer browser...');
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900 });

  const BASE_URL = 'http://localhost:5173';

  // 1. Nutella Alternatives Page
  console.log('Checking Nutella Alternatives...');
  await page.goto(`${BASE_URL}/alternatives/3017620422003`, { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'nutella_alternatives_fixed.png'), fullPage: true });

  // 2. Nutella Product Analysis - Nutrition Tab
  console.log('Checking Nutella Nutrition Tab...');
  await page.goto(`${BASE_URL}/products/3017620422003`, { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));

  // Click Nutrition Tab
  const buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text && text.includes('Nutrition Facts')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'nutella_nutrition_fixed.png'), fullPage: true });

  // 3. Nutella Product Analysis - Ingredients Tab
  console.log('Checking Nutella Ingredients Tab...');
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text && text.includes('Ingredients & Additives')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'nutella_ingredients_fixed.png'), fullPage: true });

  // 4. Another Product - Britannia Marie Gold (8901063012234 or similar in DB)
  console.log('Checking Another Product (e.g. 8901030383701 or 5449000000996)...');
  await page.goto(`${BASE_URL}/products/5449000000996`, { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1500));
  const newButtons = await page.$$('button');
  for (const btn of newButtons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text && text.includes('Nutrition Facts')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'coke_nutrition_fixed.png'), fullPage: true });

  for (const btn of newButtons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text && text.includes('Ingredients & Additives')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'coke_ingredients_fixed.png'), fullPage: true });

  await browser.close();
  console.log('All verification screenshots captured successfully!');
}

verify().catch(err => {
  console.error('Error during verification:', err);
  process.exit(1);
});
