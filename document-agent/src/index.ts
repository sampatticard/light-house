import * as path from 'path';
import pino from 'pino';
import { DocumentAgentConfig, UploadOptions, DocumentRecord, SearchOptions } from './types';
import { Encryptor } from './core/encryptor';
import { Validator } from './core/validator';
import { Categorizer } from './core/categorizer';
import { Database } from './core/database';
import { LocalStorageEngine } from './engines/localStorage';
import { Uploader } from './core/uploader';
import { OCRProcessor } from './hooks/ocr';

export class DocumentAgent {
  private config: DocumentAgentConfig;
  private encryptor: Encryptor;
  private validator: Validator;
  private categorizer: Categorizer;
  private database: Database;
  private storageEngine: LocalStorageEngine;
  private uploader: Uploader;
  private ocrProcessor: OCRProcessor;
  private logger: pino.Logger;

  constructor(config: DocumentAgentConfig) {
    this.config = {
      maxFileSize: 10 * 1024 * 1024, // 10MB default
      supportedFormats: ['pdf', 'jpg', 'jpeg', 'png', 'docx'],
      enableOCR: false,
      logLevel: 'info',
      ...config
    };

    // Initialize logger
    this.logger = pino({
      level: this.config.logLevel!,
      transport: {
        target: 'pino-pretty',
        options: {
          colorize: true
        }
      }
    });

    // Initialize core components
    this.encryptor = new Encryptor(this.config.encryptionKey);
    this.validator = new Validator(this.config.supportedFormats, this.config.maxFileSize);
    this.categorizer = new Categorizer();
    this.database = new Database(path.join(this.config.storagePath, 'documents.db'));
    this.storageEngine = new LocalStorageEngine(path.join(this.config.storagePath, 'files'));
    this.uploader = new Uploader(
      this.encryptor,
      this.validator,
      this.categorizer,
      this.database,
      this.storageEngine,
      this.config.enableOCR
    );
    this.ocrProcessor = new OCRProcessor();

    this.logger.info('DocumentAgent initialized successfully');
  }

  async upload(options: UploadOptions): Promise<DocumentRecord> {
    this.logger.info(`Uploading document for user: ${options.userId}`);
    
    try {
      const document = await this.uploader.uploadDocument(options);
      this.logger.info(`Document uploaded successfully: ${document.id}`);
      return document;
    } catch (error) {
      if (error instanceof Error) {
        this.logger.error(`Upload failed: ${error.message}`);
      } else {
        this.logger.error(`Upload failed: ${JSON.stringify(error)}`);
      }
      throw error;
    }
  }

  async getDocuments(userId: string, options: SearchOptions = {}): Promise<DocumentRecord[]> {
    this.logger.debug(`Retrieving documents for user: ${userId}`);
    
    try {
      const documents = await this.database.getDocuments(userId, options);
      this.logger.debug(`Found ${documents.length} documents`);
      return documents;
    } catch (error) {
      if (error instanceof Error) {
        this.logger.error(`Upload failed: ${error.message}`);
      } else {
        this.logger.error(`Upload failed: ${JSON.stringify(error)}`);
      }
      throw error;
    }
  }

  async getDocumentById(documentId: string): Promise<DocumentRecord | null> {
    this.logger.debug(`Retrieving document: ${documentId}`);
    
    try {
      const document = await this.database.getDocumentById(documentId);
      return document;
    } catch (error) {
      if (error instanceof Error) {
        this.logger.error(`Upload failed: ${error.message}`);
      } else {
        this.logger.error(`Upload failed: ${JSON.stringify(error)}`);
      }
      throw error;
    }
  }

  async getDocumentData(documentId: string): Promise<Buffer> {
    this.logger.debug(`Retrieving document data: ${documentId}`);
    
    try {
      const data = await this.uploader.getDocumentData(documentId);
      this.logger.debug(`Document data retrieved successfully`);
      return data;
    } catch (error) {
      if (error instanceof Error) {
        this.logger.error(`Upload failed: ${error.message}`);
      } else {
        this.logger.error(`Upload failed: ${JSON.stringify(error)}`);
      }
      throw error;
    }
  }

  async deleteDocument(documentId: string): Promise<void> {
    this.logger.info(`Deleting document: ${documentId}`);
    
    try {
      await this.uploader.deleteDocument(documentId);
      this.logger.info(`Document deleted successfully`);
    } catch (error) {
      if (error instanceof Error) {
        this.logger.error(`Upload failed: ${error.message}`);
      } else {
        this.logger.error(`Upload failed: ${JSON.stringify(error)}`);
      }
      throw error;
    }
  }

  async searchDocuments(userId: string, searchTerm: string): Promise<DocumentRecord[]> {
    this.logger.debug(`Searching documents for user: ${userId}, term: ${searchTerm}`);
    
    try {
      const documents = await this.database.searchDocuments(userId, searchTerm);
      this.logger.debug(`Found ${documents.length} matching documents`);
      return documents;
    } catch (error) {
      if (error instanceof Error) {
        this.logger.error(`Upload failed: ${error.message}`);
      } else {
        this.logger.error(`Upload failed: ${JSON.stringify(error)}`);
      }
      throw error;
    }
  }

  async addCategory(name: string, rules: RegExp[]): Promise<void> {
    this.logger.info(`Adding category: ${name}`);
    this.categorizer.addCategory(name, rules);
  }

  async removeCategory(name: string): Promise<void> {
    this.logger.info(`Removing category: ${name}`);
    this.categorizer.removeCategory(name);
  }

  getCategories(): string[] {
    return this.categorizer.getCategories();
  }

  getEncryptionKey(): string {
    return this.encryptor.getKeyHex();
  }

  async cleanup(): Promise<void> {
    this.logger.info('Cleaning up DocumentAgent resources');
    
    try {
      await this.ocrProcessor.terminate();
      this.database.close();
      this.logger.info('Cleanup completed successfully');
    } catch (error) {
      if (error instanceof Error) {
        this.logger.error(`Upload failed: ${error.message}`);
      } else {
        this.logger.error(`Upload failed: ${JSON.stringify(error)}`);
      }
      throw error;
    }
  }
}

// Export types and main class
export * from './types';
export { DocumentAgent as default };

// Example usage and testing
export const createDocumentAgent = (config: DocumentAgentConfig): DocumentAgent => {
  return new DocumentAgent(config);
};