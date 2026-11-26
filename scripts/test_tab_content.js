const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  await page.goto('http://127.0.0.1:5173/products/3017620422003', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1000));
  
  // Click Nutrition tab
  const buttons = await page.$$('button');
  for (const b of buttons) {
    const text = await (await b.getProperty('innerText')).jsonValue();
    if (text && text.includes('Nutrition Facts')) {
      await b.click();
      await new Promise(r => setTimeout(r, 500));
    }
  }
  const tableText = await page.evaluate(() => document.querySelector('table')?.innerText);
  console.log('TABLE TEXT:\n', tableText);

  // Click Ingredients tab
  for (const b of buttons) {
    const text = await (await b.getProperty('innerText')).jsonValue();
    if (text && text.includes('Ingredients')) {
      await b.click();
      await new Promise(r => setTimeout(r, 500));
    }
  }
  const allText = await page.evaluate(() => document.body.innerText);
  console.log('PAGE TEXT INGREDIENTS:\n', allText.substring(allText.indexOf('Ingredient Hierarchy')));

  await browser.close();
})();
