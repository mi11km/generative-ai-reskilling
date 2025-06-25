/// <reference types="vitest" />
import { defineConfig } from 'vite'
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [
    tsconfigPaths(),
  ],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './app/test-setup.ts',
    include: ['./app/**/*.{test,spec}.{js,ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'app/test-setup.ts',
        '**/*.d.ts',
        'build/',
        'public/',
      ],
    },
  },
})