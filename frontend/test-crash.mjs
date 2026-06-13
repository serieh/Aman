import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.error('PAGE ERROR:', err.toString()));
  
  console.log("Navigating to login...");
  await page.goto('http://localhost:5173/login');
  await page.waitForSelector('input[type="email"]');
  await page.type('input[type="email"]', 'aman@example.com');
  await page.type('input[type="password"]', 'aman123');
  await page.click('button[type="submit"]');
  
  console.log("Waiting for dashboard...");
  await page.waitForNavigation();
  
  console.log("Opening new chat...");
  await page.goto('http://localhost:5173/app/chat/temp');
  await new Promise(r => setTimeout(r, 2000));
  
  console.log("Reloading...");
  await page.reload();
  await new Promise(r => setTimeout(r, 2000));
  
  await browser.close();
  console.log("Done");
})();
