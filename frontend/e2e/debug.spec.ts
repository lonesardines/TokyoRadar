import { test, expect } from '@playwright/test';

test('debug: check API calls and console', async ({ page }) => {
  const consoleMessages: string[] = [];
  const failedRequests: string[] = [];
  const responses: { url: string; status: number }[] = [];

  page.on('console', msg => consoleMessages.push(`${msg.type()}: ${msg.text()}`));
  page.on('pageerror', err => consoleMessages.push(`PAGE_ERROR: ${err.message}`));
  page.on('requestfailed', req => failedRequests.push(`FAILED: ${req.url()} - ${req.failure()?.errorText}`));
  page.on('response', resp => {
    if (resp.url().includes('/api/')) {
      responses.push({ url: resp.url(), status: resp.status() });
    }
  });

  await page.goto('/brands');
  await page.waitForTimeout(10000);

  console.log('\n=== CONSOLE MESSAGES ===');
  for (const msg of consoleMessages) console.log(msg);
  console.log('\n=== FAILED REQUESTS ===');
  for (const req of failedRequests) console.log(req);
  console.log('\n=== API RESPONSES ===');
  for (const resp of responses) console.log(`${resp.status} ${resp.url}`);

  // Try direct fetch from the page context
  const result = await page.evaluate(async () => {
    try {
      const resp = await fetch('/api/v1/brands?per_page=1');
      const text = await resp.text();
      return { status: resp.status, body: text.substring(0, 200) };
    } catch (e: any) {
      return { error: e.message };
    }
  });
  console.log('\n=== DIRECT FETCH FROM PAGE ===');
  console.log(JSON.stringify(result, null, 2));

  expect(true).toBe(true);
});
