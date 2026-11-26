const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
  page.on('requestfailed', req => console.log('REQUEST FAILED:', req.url(), req.failure()?.errorText));

  console.log('--- Navigating to /products/3017620422003 ---');
  await page.goto('http://127.0.0.1:5173/products/3017620422003', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1000));

  const buttons = await page.$$('button');
  for (const b of buttons) {
    const text = await (await b.getProperty('innerText')).jsonValue();
    if (text && text.includes('Nutrition Facts')) {
      console.log('Clicking tab:', text);
      await b.click();
      await new Promise(r => setTimeout(r, 500));
      await page.screenshot({ path: 'test_tab_nutrition.png' });
    }
  }
  for (const b of buttons) {
    const text = await (await b.getProperty('innerText')).jsonValue();
    if (text && text.includes('Ingredients')) {
      console.log('Clicking tab:', text);
      await b.click();
      await new Promise(r => setTimeout(r, 500));
      await page.screenshot({ path: 'test_tab_ingredients.png' });
    }
  }

  console.log('--- Navigating to /alternatives/3017620422003 ---');
  await page.goto('http://127.0.0.1:5173/alternatives/3017620422003', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: 'test_alternatives_nutella.png' });

  const bodyText = await page.evaluate(() => document.body.innerText);
  console.log('Alternatives page preview:');
  console.log(bodyText.substring(0, 1000));

  await browser.close();
  console.log('Finished debug test');
})();
