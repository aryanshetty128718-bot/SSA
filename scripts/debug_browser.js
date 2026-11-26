const puppeteer = require('../frontend/node_modules/puppeteer');

async function debugPage() {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  page.on('console', msg => console.log('BROWSER LOG:', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err));
  page.on('requestfailed', req => console.log('REQUEST FAILED:', req.url(), req.failure()?.errorText));
  page.on('response', async resp => {
    if (resp.url().includes('/api/v1')) {
      console.log('API RESP:', resp.status(), resp.url());
      try {
        const txt = await resp.text();
        console.log('BODY PREVIEW:', txt.substring(0, 200));
      } catch (e) {}
    }
  });

  console.log('Navigating to Nutella analysis...');
  await page.goto('http://127.0.0.1:5173/products/3017620422003', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 2000));

  const state = await page.evaluate(() => {
    return {
      h1: document.querySelector('h1')?.textContent,
      buttons: Array.from(document.querySelectorAll('button')).map(b => b.textContent)
    };
  });
  console.log('PAGE STATE:', state);

  // Click nutrition
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const b = btns.find(el => el.textContent && el.textContent.includes('Nutrition Facts'));
    if (b) b.click();
  });
  await new Promise(r => setTimeout(r, 1000));

  const nutrHtml = await page.evaluate(() => {
    const heading = Array.from(document.querySelectorAll('h3')).find(h => h.textContent.includes('Nutritional Declaration'));
    return heading?.parentElement?.innerHTML;
  });
  console.log('NUTR TAB HTML:', nutrHtml);

  // Click ingredients
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const b = btns.find(el => el.textContent && el.textContent.includes('Ingredients & Additives'));
    if (b) b.click();
  });
  await new Promise(r => setTimeout(r, 1000));

  const ingHtml = await page.evaluate(() => {
    const heading = Array.from(document.querySelectorAll('h3')).find(h => h.textContent.includes('Ingredient Hierarchy'));
    return heading?.parentElement?.innerHTML;
  });
  console.log('ING TAB HTML:', ingHtml);

  // Now navigate to alternatives
  console.log('\nNavigating to Nutella alternatives...');
  await page.goto('http://127.0.0.1:5173/alternatives/3017620422003', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 2000));

  const altState = await page.evaluate(() => {
    return {
      cardsCount: document.querySelectorAll('.grid > div').length,
      bodyText: document.body.innerText
    };
  });
  console.log('ALT STATE cardsCount:', altState.cardsCount);
  console.log('ALT BODY SNIPPET:\n', altState.bodyText.substring(0, 500));

  await browser.close();
}

debugPage().catch(console.error);
