/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // Only our own tests -- never node_modules or build output.
    include: ['src/**/*.test.{ts,tsx}'],
    // Form-driven tests do real user-event typing and full route renders;
    // the default 5s is tight once several files run in parallel.
    testTimeout: 20000,
  },
})
