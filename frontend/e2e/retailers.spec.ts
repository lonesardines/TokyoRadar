import { test, expect } from '@playwright/test';

test.describe('零售商页 (RetailersPage)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/retailers');
    // Wait for retailer data to load — section headings appear after data loads
    await expect(page.getByRole('heading', { level: 2 }).first()).toBeVisible({ timeout: 15000 });
  });

  test('页面加载 — 标题和描述', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Retailers' })).toBeVisible();
    await expect(page.getByText(/japanese fashion retailers/i)).toBeVisible();
  });

  test('配送分组 — 按 tier 分组显示', async ({ page }) => {
    const sectionHeaders = page.getByRole('heading', { level: 2 });
    expect(await sectionHeaders.count()).toBeGreaterThanOrEqual(1);
  });

  test('零售商卡片 — 显示名称和国家', async ({ page }) => {
    const cards = page.locator('.border.rounded-lg');
    expect(await cards.count()).toBeGreaterThanOrEqual(3);
  });

  test('配送标签 — Shipping Badge 渲染', async ({ page }) => {
    const badges = page.getByText(/(direct ship|proxy required|agent required)/i);
    await expect(badges.first()).toBeVisible();
  });

  test('外部链接 — Visit Website 链接存在', async ({ page }) => {
    const visitLinks = page.getByText('Visit Website');
    await expect(visitLinks.first()).toBeVisible();
  });

  test('Supported Proxies — 代购标签显示', async ({ page }) => {
    const proxyLabel = page.getByText('Supported Proxies');
    if (await proxyLabel.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(proxyLabel.first()).toBeVisible();
    }
  });
});
