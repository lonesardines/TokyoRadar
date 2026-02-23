import { test, expect } from '@playwright/test';

test.describe('首页 (HomePage)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('页面加载 — 标题和 hero 区域', async ({ page }) => {
    // Hero 标题
    const heroHeading = page.getByRole('heading', { name: /TOKYO\s*RADAR/i });
    await expect(heroHeading).toBeVisible();

    // 副标题 — scope to main to avoid footer match
    const main = page.locator('main');
    await expect(main.getByText(/intelligence.*japanese fashion/i)).toBeVisible();
  });

  test('导航链接可见', async ({ page }) => {
    const header = page.locator('header');
    await expect(header.getByRole('link', { name: /brands/i })).toBeVisible();
    await expect(header.getByRole('link', { name: /retailers/i })).toBeVisible();
    await expect(header.getByRole('link', { name: /buy guide/i })).toBeVisible();
  });

  test('CTA 按钮 — Explore Brands 跳转', async ({ page }) => {
    await page.getByRole('link', { name: /explore brands/i }).click();
    await expect(page).toHaveURL(/\/brands/);
  });

  test('CTA 按钮 — Buy Guide 跳转', async ({ page }) => {
    await page.getByRole('link', { name: /buy guide/i }).first().click();
    await expect(page).toHaveURL(/\/buy-guide/);
  });

  test('Editor\'s Picks — 加载品牌卡片', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /editor.*pick/i })).toBeVisible();

    // Wait for brand cards to load (BrandCard renders as Link to="/brands/slug")
    const brandLinks = page.locator('a[href^="/brands/"]');
    await expect(brandLinks.first()).toBeVisible({ timeout: 15000 });
    expect(await brandLinks.count()).toBeGreaterThanOrEqual(1);
  });

  test('Browse by Style — 分类卡片', async ({ page }) => {
    const heading = page.getByRole('heading', { name: /browse by style/i });
    await expect(heading).toBeVisible();

    // Scope to the Browse by Style section to avoid matching StyleTags in brand cards
    const section = heading.locator('..').locator('..');
    for (const cat of ['Streetwear', 'Avant-Garde', 'Denim', 'Workwear']) {
      await expect(section.getByText(cat, { exact: false }).first()).toBeVisible();
    }
  });

  test('Browse by Style — 点击分类跳转到筛选后的品牌页', async ({ page }) => {
    await page.locator('a[href*="style=streetwear"]').click();
    await expect(page).toHaveURL(/\/brands\?.*style=streetwear/i);
  });

  test('Stats bar — 数据统计', async ({ page }) => {
    await expect(page.getByText('50+')).toBeVisible();
    await expect(page.getByText('10+')).toBeVisible();
  });

  test('Footer 存在', async ({ page }) => {
    const footer = page.locator('footer');
    await expect(footer).toBeVisible();
    await expect(footer.getByText(/tokyoradar/i)).toBeVisible();
  });
});
