import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  fullyParallel: false,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: process.env.E2E_FRONTEND_URL ?? "http://localhost:3000",
    channel: "chrome",
    headless: true,
    trace: "retain-on-failure",
  },
});
