import { defineConfig, devices } from '@playwright/test';

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
import dotenv from 'dotenv';
import path from 'path';
dotenv.config({ path: path.resolve(__dirname, '.env') });

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: './tests',
  /* Downloads the backend API schema for the contract checks of the fake backend */
  globalSetup: './tests/global-setup.ts',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Tests mostly wait for the backend, so CI runs more workers than its cores. Locally all workers share one `next dev` server, which compiles routes on first request */
  workers: process.env.CI ? 4 : 2,
  /* Pages are not prerendered in tests (`next dev` locally, PLAYWRIGHT_TEST build on CI), so the first visit renders them from the backend and can take longer than the default 5s */
  expect: { timeout: 15000 },
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: 'html',
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('')`. */
    baseURL: 'http://127.0.0.1:4004',

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    /*
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    */

    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    
    /*
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
    */
  ],

  webServer: {
    command: process.env.CI ? 'PORT=4004 node .next/standalone/server.js' : 'npm run test',
    url: 'http://127.0.0.1:4004',
    reuseExistingServer: !process.env.CI,
  },
});
