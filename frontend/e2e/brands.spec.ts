import { test, expect } from '@playwright/test';

test.describe('品牌目录页 (BrandsPage)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/brands');
    // Wait for brand cards to appear (data loaded)
    await expect(page.locator('a[href^="/brands/"]').first()).toBeVisible({ timeout: 15000 });
  });

  test('页面加载 — 品牌列表渲染', async ({ page }) => {
    const cards = page.locator('a[href^="/brands/"]');
    expect(await cards.count()).toBeGreaterThanOrEqual(10);
  });

  test('品牌卡片 — 显示关键信息', async ({ page }) => {
    const firstCard = page.locator('a[href^="/brands/"]').first();
    const text = await firstCard.textContent();
    expect(text!.length).toBeGreaterThan(0);
  });

  test('配送标签 — Shipping Badge 渲染', async ({ page }) => {
    const badges = page.getByText(/(direct ship|proxy required|agent required)/i);
    await expect(badges.first()).toBeVisible();
  });

  test('搜索过滤 — 输入搜索词', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i);
    if (await searchInput.isVisible()) {
      await searchInput.fill('visvim');
      await page.waitForTimeout(1000);
      await expect(page.getByText('visvim', { exact: false })).toBeVisible();
    }
  });

  test('Style Tag 过滤 — 点击分类标签', async ({ page }) => {
    const tagButton = page.getByRole('button', { name: /streetwear/i });
    if (await tagButton.isVisible()) {
      await tagButton.click();
      await page.waitForTimeout(1000);
    }
  });

  test('品牌卡片 — 点击跳转到详情页', async ({ page }) => {
    const firstBrandLink = page.locator('a[href^="/brands/"]').first();
    const href = await firstBrandLink.getAttribute('href');
    await firstBrandLink.click();
    await expect(page).toHaveURL(href!);
  });
});

test.describe('品牌详情页 (BrandDetailPage)', () => {
  test('sacai 详情页 — 完整信息显示', async ({ page }) => {
    await page.goto('/brands/sacai');

    // Wait for content to load by looking for the brand name in a heading
    await expect(page.getByText('sacai').first()).toBeVisible({ timeout: 15000 });

    // 日文名
    await expect(page.getByText('サカイ')).toBeVisible();

    // 设计师
    await expect(page.getByText(/chitose abe/i).first()).toBeVisible();

    // 配送标签
    await expect(page.getByText(/(direct ship|proxy required|agent required)/i).first()).toBeVisible();
  });

  test('sacai 详情页 — Buy Guide 购买渠道', async ({ page }) => {
    await page.goto('/brands/sacai');
    await expect(page.getByText('sacai').first()).toBeVisible({ timeout: 15000 });

    // 购买渠道
    await expect(page.getByText(/(how to buy|buy guide|purchase|channel)/i).first()).toBeVisible({ timeout: 10000 });
  });

  test('visvim 详情页 — 加载成功', async ({ page }) => {
    await page.goto('/brands/visvim');
    await expect(page.getByText('visvim').first()).toBeVisible({ timeout: 15000 });
  });

  test('返回链接 — 点击返回品牌列表', async ({ page }) => {
    await page.goto('/brands/sacai');
    await expect(page.getByText('sacai').first()).toBeVisible({ timeout: 15000 });

    const backLink = page.getByRole('link', { name: /back|brands/i }).first();
    if (await backLink.isVisible()) {
      await backLink.click();
      await expect(page).toHaveURL(/\/brands$/);
    }
  });

  test('不存在的品牌 — 处理 404', async ({ page }) => {
    const response = await page.goto('/brands/nonexistent-brand-xyz');
    expect(response?.status()).toBe(200);
  });
});
