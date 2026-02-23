import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:5174',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
  // Start a local Vite dev server for E2E tests
  // VITE_API_URL points browser directly to backend (bypasses Vite proxy)
  webServer: {
    command: 'VITE_API_PROXY_TARGET=http://localhost:8000 npx vite --port 5174',
    port: 5174,
    reuseExistingServer: !process.env.CI,
    timeout: 30000,
  },
});
