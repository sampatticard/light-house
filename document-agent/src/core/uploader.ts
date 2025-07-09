import * as fs from 'fs';
import * as path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { DocumentRecord, UploadOptions } from '../types';
import { Encryptor } from './encryptor';
import { Validator } from './validator';
import { Categorizer } from './categorizer';
import { Database } from './database';
import { StorageEngine } from '../types';
import { OCRProcessor } from '../hooks/ocr';

export class Uploader {
  private encryptor: Encryptor;
  private validator: Validator;
  private categorizer: Categorizer;
  private database: Database;
  private storageEngine: StorageEngine;
  private ocrProcessor: OCRProcessor;
  private enableOCR: boolean;

  constructor(
    encryptor: Encryptor,
    validator: Validator,
    categorizer: Categorizer,
    database: Database,
    storageEngine: StorageEngine,
    enableOCR: boolean = false
  ) {
    this.encryptor = encryptor;
    this.validator = validator;
    this.categorizer = categorizer;
    this.database = database;
    this.storageEngine = storageEngine;
    this.enableOCR = enableOCR;
    this.ocrProcessor = new OCRProcessor();
  }

  async uploadDocument(options: UploadOptions): Promise<DocumentRecord> {
    const { file, category, userId, metadata = {}, enableOCR = this.enableOCR } = options;
    
    // Read file data
    let fileBuffer: Buffer;
    let originalName: string;
    
    if (typeof file === 'string') {
      // File path
      fileBuffer = fs.readFileSync(file);
      originalName = path.basename(file);
    } else {
      // Buffer
      fileBuffer = file;
      originalName = metadata.originalName || 'unknown';
    }

    // Validate file
    const validation = await this.validator.validateBuffer(fileBuffer, originalName);
    if (!validation.isValid) {
      throw new Error(validation.error);
    }

    // Generate document ID and hash
    const docId = uuidv4();
    const hash = this.encryptor.generateHash(fileBuffer);

    // Check for duplicates
    const existingDocs = await this.database.getDocuments(userId);
    const duplicate = existingDocs.find(doc => doc.hash === hash);
    if (duplicate) {
      throw new Error('Document already exists');
    }

    // Auto-categorize if not provided
    let finalCategory = category;
    if (!finalCategory) {
      finalCategory = this.categorizer.categorize(originalName);
    }

    // OCR processing if enabled
    let ocrText = '';
    if (enableOCR && ['pdf', 'jpg', 'jpeg', 'png'].includes(validation.fileType!)) {
      try {
        ocrText = await this.ocrProcessor.processDocument(fileBuffer, validation.fileType!);
      } catch (error) {
        console.warn('OCR processing failed:', error);
      }
    }

    // Encrypt file
    const { encrypted, iv, tag } = this.encryptor.encrypt(fileBuffer);
    const encryptedData = Buffer.concat([
      Buffer.from(JSON.stringify({ iv: iv.toString('hex'), tag: tag.toString('hex') })),
      Buffer.from('\n---SEPARATOR---\n'),
      encrypted
    ]);

    // Store encrypted file
    const encryptedPath = await this.storageEngine.store(userId, docId, encryptedData);

    // Create document record
    const documentRecord: DocumentRecord = {
      id: docId,
      userId,
      originalName,
      category: finalCategory,
      fileType: validation.fileType!,
      size: fileBuffer.length,
      hash,
      encryptedPath,
      metadata,
      ocrText,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    // Save to database
    await this.database.insertDocument(documentRecord);

    return documentRecord;
  }

  async getDocumentData(documentId: string): Promise<Buffer> {
    const document = await this.database.getDocumentById(documentId);
    if (!document) {
      throw new Error('Document not found');
    }

    // Retrieve encrypted data
    const encryptedData = await this.storageEngine.retrieve(document.userId, document.encryptedPath);
    
    // Parse encryption metadata
    const separatorIndex = encryptedData.indexOf('\n---SEPARATOR---\n');
    if (separatorIndex === -1) {
      throw new Error('Invalid encrypted file format');
    }

    const metadataStr = encryptedData.slice(0, separatorIndex).toString();
    const encryptedContent = encryptedData.slice(separatorIndex + '\n---SEPARATOR---\n'.length);
    
    const { iv, tag } = JSON.parse(metadataStr);
    
    // Decrypt file
    const decrypted = this.encryptor.decrypt(
      encryptedContent,
      Buffer.from(iv, 'hex'),
      Buffer.from(tag, 'hex')
    );

    return decrypted;
  }

  async deleteDocument(documentId: string): Promise<void> {
    const document = await this.database.getDocumentById(documentId);
    if (!document) {
      throw new Error('Document not found');
    }

    // Delete from storage
    await this.storageEngine.delete(document.userId, document.encryptedPath);
    
    // Delete from database
    await this.database.deleteDocument(documentId);
  }
}