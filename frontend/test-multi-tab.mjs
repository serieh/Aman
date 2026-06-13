import puppeteer from 'puppeteer';

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  
  const page1 = await browser.newPage();
  page1.on('console', msg => console.log('TAB 1:', msg.text()));
  page1.on('pageerror', err => console.log('TAB 1 CRASH:', err.toString()));
  
  await page1.goto('http://localhost:5173/login');
  await page1.waitForSelector('input[type="email"]');
  await page1.type('input[type="email"]', 'aman@example.com');
  await page1.type('input[type="password"]', 'aman123');
  await page1.click('button[type="submit"]');
  await page1.waitForNavigation();
  
  await page1.goto('http://localhost:5173/app/chat/temp');
  await new Promise(r => setTimeout(r, 2000));
  
  console.log("Creating new tab...");
  const page2 = await browser.newPage();
  page2.on('console', msg => console.log('TAB 2:', msg.text()));
  page2.on('pageerror', err => console.log('TAB 2 CRASH:', err.toString()));
  
  const url = page1.url();
  console.log("Tab 1 URL:", url);
  await page2.goto(url);
  
  await new Promise(r => setTimeout(r, 3000));
  
  // Dump the HTML of Tab 2
  const html = await page2.content();
  console.log("Tab 2 HTML length:", html.length);
  if (html.length < 500) console.log(html);
  
  // Refresh Tab 1
  console.log("Refreshing Tab 1...");
  await page1.reload();
  await new Promise(r => setTimeout(r, 3000));
  const html1 = await page1.content();
  console.log("Tab 1 HTML length:", html1.length);
  if (html1.length < 500) console.log(html1);

  await browser.close();
  console.log("Done");
})();
