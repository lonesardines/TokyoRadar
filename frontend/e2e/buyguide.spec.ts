import { test, expect } from '@playwright/test';

test.describe('购买指南页 (BuyGuidePage)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/buy-guide');
    // Wait for proxy service cards to load
    await expect(page.getByText(/^Visit /).first()).toBeVisible({ timeout: 15000 });
  });

  test('页面加载 — 标题和描述', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Buy Guide' })).toBeVisible();
    await expect(page.getByText(/proxy and forwarding services/i)).toBeVisible();
  });

  test('Shipping Tier 图例 — 三种配送标签说明', async ({ page }) => {
    await expect(page.getByText('Shipping Tier Guide')).toBeVisible();
    await expect(page.getByText('Direct Ship')).toBeVisible();
    await expect(page.getByText('Proxy Required')).toBeVisible();
    await expect(page.getByText('Agent Required')).toBeVisible();
  });

  test('代购服务卡片 — 加载并显示', async ({ page }) => {
    const serviceCards = page.locator('.border.rounded-lg');
    expect(await serviceCards.count()).toBeGreaterThanOrEqual(2);
  });

  test('代购服务 — 显示服务类型', async ({ page }) => {
    const typeLabels = page.getByText(/(proxy buying|package forwarding|proxy \+ forwarding)/i);
    await expect(typeLabels.first()).toBeVisible();
  });

  test('代购服务 — 配送时间显示', async ({ page }) => {
    const daysText = page.getByText(/days/);
    await expect(daysText.first()).toBeVisible();
  });

  test('代购服务 — Fee Structure 显示', async ({ page }) => {
    const feeLabel = page.getByText('Fee Structure');
    await expect(feeLabel.first()).toBeVisible();
  });

  test('代购服务 — Pros & Cons 显示', async ({ page }) => {
    await expect(page.getByText('Pros').first()).toBeVisible();
    await expect(page.getByText('Cons').first()).toBeVisible();
  });

  test('代购服务 — 外部链接', async ({ page }) => {
    const visitLinks = page.getByText(/^Visit /);
    await expect(visitLinks.first()).toBeVisible();
  });
});
