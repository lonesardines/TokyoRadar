import { test, expect } from '@playwright/test';

test.describe('语言切换 (i18n)', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage to ensure clean state
    await page.goto('/');
    await page.evaluate(() => localStorage.removeItem('locale'));
    await page.reload();
  });

  test('默认语言为英文', async ({ page }) => {
    const header = page.locator('header');
    await expect(header.getByRole('link', { name: 'Brands' })).toBeVisible();
    await expect(header.getByRole('link', { name: 'Retailers' })).toBeVisible();
    await expect(header.getByRole('link', { name: 'Buy Guide' })).toBeVisible();

    // Hero text in English
    await expect(page.getByText('Japanese Fashion Intelligence')).toBeVisible();
    await expect(page.getByRole('link', { name: /Explore Brands/i })).toBeVisible();
  });

  test('点击「中」切换到中文', async ({ page }) => {
    await page.getByRole('button', { name: '中' }).first().click();

    // Nav should be in Chinese
    const header = page.locator('header');
    await expect(header.getByRole('link', { name: '品牌' })).toBeVisible();
    await expect(header.getByRole('link', { name: '零售商' })).toBeVisible();
    await expect(header.getByRole('link', { name: '购买指南' })).toBeVisible();

    // Hero text in Chinese
    await expect(page.getByText('日本时尚情报')).toBeVisible();
    await expect(page.getByRole('link', { name: /探索品牌/i })).toBeVisible();
  });

  test('点击「EN」切回英文', async ({ page }) => {
    // Switch to Chinese first
    await page.getByRole('button', { name: '中' }).first().click();
    await expect(page.locator('header').getByRole('link', { name: '品牌' })).toBeVisible();

    // Switch back to English
    await page.getByRole('button', { name: 'EN' }).first().click();
    await expect(page.locator('header').getByRole('link', { name: 'Brands' })).toBeVisible();
    await expect(page.getByText('Japanese Fashion Intelligence')).toBeVisible();
  });

  test('刷新页面后语言保持 (localStorage)', async ({ page }) => {
    // Switch to Chinese
    await page.getByRole('button', { name: '中' }).first().click();
    await expect(page.locator('header').getByRole('link', { name: '品牌' })).toBeVisible();

    // Reload page
    await page.reload();

    // Should still be Chinese
    await expect(page.locator('header').getByRole('link', { name: '品牌' })).toBeVisible();
    await expect(page.locator('header').getByRole('link', { name: '零售商' })).toBeVisible();
    await expect(page.getByText('日本时尚情报')).toBeVisible();
  });

  test('切换语言后导航到其他页面 — 语言保持', async ({ page }) => {
    // Switch to Chinese on home page
    await page.getByRole('button', { name: '中' }).first().click();
    await expect(page.locator('header').getByRole('link', { name: '品牌' })).toBeVisible();

    // Navigate to brands page
    await page.locator('header').getByRole('link', { name: '品牌' }).click();
    await expect(page).toHaveURL(/\/brands/);
    await expect(page.getByText('全部品牌')).toBeVisible();
    await expect(page.getByText('目录')).toBeVisible();

    // Navigate to retailers page
    await page.locator('header').getByRole('link', { name: '零售商' }).click();
    await expect(page).toHaveURL(/\/retailers/);
    await expect(page.getByRole('heading', { name: '零售商' })).toBeVisible();

    // Navigate to buy guide page
    await page.locator('header').getByRole('link', { name: '购买指南' }).click();
    await expect(page).toHaveURL(/\/buy-guide/);
    await expect(page.getByRole('heading', { name: '购买指南' })).toBeVisible();
  });
});
