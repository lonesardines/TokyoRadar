import { test, expect } from '@playwright/test';

test.describe('全局导航与路由 (Navigation)', () => {
  test('Header 导航 — 品牌页', async ({ page }) => {
    await page.goto('/');
    const header = page.locator('header');
    await header.getByRole('link', { name: /brands/i }).click();
    await expect(page).toHaveURL(/\/brands$/);
  });

  test('Header 导航 — 零售商页', async ({ page }) => {
    await page.goto('/');
    const header = page.locator('header');
    await header.getByRole('link', { name: /retailers/i }).click();
    await expect(page).toHaveURL(/\/retailers/);
  });

  test('Header 导航 — 购买指南页', async ({ page }) => {
    await page.goto('/');
    const header = page.locator('header');
    await header.getByRole('link', { name: /buy guide/i }).click();
    await expect(page).toHaveURL(/\/buy-guide/);
  });

  test('404 页面 — 不存在的路由', async ({ page }) => {
    await page.goto('/this-route-does-not-exist');
    await expect(page.getByText('404')).toBeVisible();
    await expect(page.getByText('Page Not Found')).toBeVisible();
  });

  test('404 页面 — Back to Home 链接', async ({ page }) => {
    await page.goto('/this-route-does-not-exist');
    await expect(page.getByText('Back to Home')).toBeVisible();
    await page.getByText('Back to Home').click();
    await expect(page).toHaveURL('/');
  });

  test('Layout — Header 和 Footer 始终存在', async ({ page }) => {
    // 首页
    await page.goto('/');
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('footer')).toBeVisible();

    // 品牌页
    await page.goto('/brands');
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('footer')).toBeVisible();

    // 零售商页
    await page.goto('/retailers');
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('footer')).toBeVisible();

    // 购买指南
    await page.goto('/buy-guide');
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('footer')).toBeVisible();

    // 404
    await page.goto('/non-existent');
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('footer')).toBeVisible();
  });

  test('Logo 点击 — 返回首页', async ({ page }) => {
    await page.goto('/brands');
    // Logo 通常是第一个指向 / 的链接
    const logoLink = page.locator('header a[href="/"]').first();
    if (await logoLink.isVisible()) {
      await logoLink.click();
      await expect(page).toHaveURL('/');
    }
  });
});
