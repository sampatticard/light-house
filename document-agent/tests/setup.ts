import * as fs from 'fs';
import * as path from 'path';

// Global test setup
beforeAll(() => {
  // Create test directories
  const testDir = path.join(__dirname, '..', 'test-data');
  if (!fs.existsSync(testDir)) {
    fs.mkdirSync(testDir, { recursive: true });
  }
});

afterAll(() => {
  // Cleanup test directories
  const testDir = path.join(__dirname, '..', 'test-data');
  if (fs.existsSync(testDir)) {
    fs.rmSync(testDir, { recursive: true, force: true });
  }
});
