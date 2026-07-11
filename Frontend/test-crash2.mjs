import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('REACT CRASH:', err.toString()));
  
  await page.goto('http://localhost:5173/login');
  await page.waitForSelector('input[type="email"]');
  await page.type('input[type="email"]', 'aman@example.com');
  await page.type('input[type="password"]', 'aman123');
  await page.click('button[type="submit"]');
  
  await page.waitForNavigation();
  
  await page.goto('http://localhost:5173/app/chat/temp');
  await new Promise(r => setTimeout(r, 2000));
  
  console.log("RELOADING PAGE NOW");
  await page.reload();
  await new Promise(r => setTimeout(r, 2000));
  
  await browser.close();
  console.log("Done");
})();
