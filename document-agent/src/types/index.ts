export interface DocumentAgentConfig {
  encryptionKey?: string;
  storagePath: string;
  enableOCR?: boolean;
  maxFileSize?: number;
  supportedFormats?: string[];
  logLevel?: 'error' | 'warn' | 'info' | 'debug';
}

export interface UploadOptions {
  file: string | Buffer;
  category?: string;
  userId: string;
  metadata?: Record<string, any>;
  enableOCR?: boolean;
}

export interface DocumentRecord {
  id: string;
  userId: string;
  originalName: string;
  category: string;
  fileType: string;
  size: number;
  hash: string;
  encryptedPath: string;
  metadata: Record<string, any>;
  ocrText?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface SearchOptions {
  category?: string;
  fileType?: string;
  dateRange?: {
    start: Date;
    end: Date;
  };
  limit?: number;
  offset?: number;
}

export interface StorageEngine {
  store(userId: string, fileId: string, encryptedData: Buffer): Promise<string>;
  retrieve(userId: string, path: string): Promise<Buffer>;
  delete(userId: string, path: string): Promise<void>;
  exists(userId: string, path: string): Promise<boolean>;
}