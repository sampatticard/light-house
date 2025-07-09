import * as fs from 'fs';
import * as path from 'path';
import { StorageEngine } from '../types';

export class LocalStorageEngine implements StorageEngine {
  private basePath: string;

  constructor(basePath: string) {
    this.basePath = basePath;
    this.ensureDirectoryExists(basePath);
  }

  private ensureDirectoryExists(dirPath: string): void {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }

  private getUserPath(userId: string): string {
    const userPath = path.join(this.basePath, userId);
    this.ensureDirectoryExists(userPath);
    return userPath;
  }

  async store(userId: string, fileId: string, encryptedData: Buffer): Promise<string> {
    const userPath = this.getUserPath(userId);
    const filePath = path.join(userPath, `${fileId}.enc`);
    
    fs.writeFileSync(filePath, encryptedData);
    return filePath;
  }

  async retrieve(userId: string, filePath: string): Promise<Buffer> {
    const fullPath = path.isAbsolute(filePath) ? filePath : path.join(this.getUserPath(userId), filePath);
    
    if (!fs.existsSync(fullPath)) {
      throw new Error(`File not found: ${fullPath}`);
    }
    
    return fs.readFileSync(fullPath);
  }

  async delete(userId: string, filePath: string): Promise<void> {
    const fullPath = path.isAbsolute(filePath) ? filePath : path.join(this.getUserPath(userId), filePath);
    
    if (fs.existsSync(fullPath)) {
      fs.unlinkSync(fullPath);
    }
  }

  async exists(userId: string, filePath: string): Promise<boolean> {
    const fullPath = path.isAbsolute(filePath) ? filePath : path.join(this.getUserPath(userId), filePath);
    return fs.existsSync(fullPath);
  }
}