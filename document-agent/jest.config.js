module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  // Run tests serially (one at a time) instead of in parallel to prevent SQLite conflicts
  maxWorkers: 1,
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  transform: {
    '^.+\\.ts$': 'ts-jest',
  },
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/index.ts'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  testTimeout: 30000,
  transformIgnorePatterns: [
    "/node_modules/(?!file-type|strtok3|peek-readable)"
  ],
};