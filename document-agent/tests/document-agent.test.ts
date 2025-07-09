import * as fs from 'fs';
import * as path from 'path';
import { DocumentAgent } from '../src/index';
import { DocumentAgentConfig } from '../src/types';

// Import Jest globals
const jestGlobals = require('@jest/globals');
const { describe, test, expect, beforeEach, afterEach } = jestGlobals;

describe('DocumentAgent', () => {
  let agent: DocumentAgent;
  let testConfig: DocumentAgentConfig;
  let testDir: string;

  beforeEach(() => {
    const randomId = Math.random().toString(36).substring(2, 10);
    testDir = path.resolve(__dirname, '..', 'test-data', `test-${Date.now()}-${randomId}`);
    
    fs.mkdirSync(testDir, { recursive: true });
    
    fs.mkdirSync(path.join(testDir, 'files'), { recursive: true });
    
    testConfig = {
      storagePath: testDir,
      encryptionKey: 'a'.repeat(64), // 32 bytes in hex
      enableOCR: false,
      maxFileSize: 5 * 1024 * 1024, // 5MB for tests
      logLevel: 'error'
    };
    
    // Create the agent with the unique test directory
    agent = new DocumentAgent(testConfig);
  });

  afterEach(async () => {
    try {
      // Try to cleanup the agent resources first
      if (agent) {
        await agent.cleanup();
      }
    } catch (err) {
      console.error(`Error during agent cleanup: ${err}`);
    } finally {
      try {
        // Give the system a moment to release any file handles
        await new Promise(resolve => setTimeout(resolve, 100));
        
        if (fs.existsSync(testDir)) {
          fs.rmSync(testDir, { recursive: true, force: true });
        }
      } catch (err) {
        console.error(`Error removing test directory: ${err}`);
      }
    }
  });

  describe('Initialization', () => {
    test('should initialize successfully with valid config', () => {
      expect(agent).toBeDefined();
      expect(agent.getCategories()).toContain('aadhaar');
      expect(agent.getCategories()).toContain('pan');
    });

    test('should use default values for optional config', async () => {
      // Use a separate directory for this test to avoid database locking issues
      const separateTestDir = path.resolve(__dirname, '..', 'test-data', `minimal-test-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`);
      fs.mkdirSync(separateTestDir, { recursive: true });
      
      try {
        const minimalConfig: DocumentAgentConfig = {
          storagePath: separateTestDir
        };
        
        const minimalAgent = new DocumentAgent(minimalConfig);
        expect(minimalAgent).toBeDefined();
        expect(minimalAgent.getEncryptionKey()).toBeDefined();
        
        await minimalAgent.cleanup();
      } finally {
        if (fs.existsSync(separateTestDir)) {
          await new Promise(resolve => setTimeout(resolve, 100));
          fs.rmSync(separateTestDir, { recursive: true, force: true });
        }
      }
    });
  });

  describe('Document Upload', () => {
    test('should upload a document successfully', async () => {
      const testFile = path.join(testDir, 'test.pdf');
      fs.writeFileSync(testFile, Buffer.from('%PDF-1.1\nTest document content\n%EOF\n'));

      const result = await agent.upload({
        file: testFile,
        userId: 'test-user-1',
        category: 'general'
      });

      expect(result.id).toBeDefined();
      expect(result.userId).toBe('test-user-1');
      expect(result.category).toBe('general');
      expect(result.originalName).toBe('test.pdf');
      expect(result.size).toBeGreaterThan(0);
      expect(result.hash).toBeDefined();
    });

    test('should auto-categorize documents', async () => {
      const testFile = path.join(testDir, 'aadhaar_card.pdf');
      fs.writeFileSync(testFile, Buffer.from('%PDF-Aadhar Card\n%EOF\n'));

      const result = await agent.upload({
        file: testFile,
        userId: 'test-user-1'
      });

      expect(result.category).toBe('aadhaar');
    });

    test('should reject oversized files', async () => {
      const testFile = path.join(testDir, 'large.pdf');
      const largeContent = '%PDF-1.1\n' + 'x'.repeat(10 * 1024 * 1024) + '\n%EOF\n'; // 10MB
      fs.writeFileSync(testFile, largeContent);

      await expect(agent.upload({
        file: testFile,
        userId: 'test-user-1'
      })).rejects.toThrow('File size exceeds limit');
    });

    test('should reject duplicate documents', async () => {
      const testFile = path.join(testDir, 'duplicate.pdf');
      fs.writeFileSync(testFile, Buffer.from('%PDF-1.1\nDuplicate content\n%EOF\n'));

      // Upload first time
      await agent.upload({
        file: testFile,
        userId: 'test-user-1'
      });

      // Upload again - should fail
      await expect(agent.upload({
        file: testFile,
        userId: 'test-user-1'
      })).rejects.toThrow('Document already exists');
    });
  });

  describe('Document Retrieval', () => {
    test('should retrieve uploaded documents', async () => {
      const testFile = path.join(testDir, 'retrieve.pdf');
      fs.writeFileSync(testFile, Buffer.from('%PDF-1.1\nRetrieve test content\n%EOF\n'));

      const uploaded = await agent.upload({
        file: testFile,
        userId: 'test-user-1'
      });

      const documents = await agent.getDocuments('test-user-1');
      expect(documents).toHaveLength(1);
      expect(documents[0].id).toBe(uploaded.id);
    });

    test('should retrieve document by ID', async () => {
      const testFile = path.join(testDir, 'byid.pdf');
      fs.writeFileSync(testFile, Buffer.from('%PDF-1.1\nBy ID test content\n%EOF\n'));

      const uploaded = await agent.upload({
        file: testFile,
        userId: 'test-user-1'
      });

      const document = await agent.getDocumentById(uploaded.id);
      expect(document).toBeDefined();
      expect(document!.id).toBe(uploaded.id);
    });

    test('should retrieve document data', async () => {
      const testContent = '%PDF-1.1\nDocument data test content\n%EOF\n';
      const testFile = path.join(testDir, 'data.pdf');
      fs.writeFileSync(testFile, testContent);

      const uploaded = await agent.upload({
        file: testFile,
        userId: 'test-user-1'
      });

      const data = await agent.getDocumentData(uploaded.id);
      expect(data.toString()).toBe(testContent);
    });

    test('should filter documents by category', async () => {
      const testFile1 = path.join(testDir, 'general.pdf');
      const testFile2 = path.join(testDir, 'aadhaar.pdf');
      
      fs.writeFileSync(testFile1, Buffer.from('%PDF-1.1\nGeneral document\n%EOF\n'));
      fs.writeFileSync(testFile2, Buffer.from('%PDF-1.1\nAadhaar document\n%EOF\n'));

      await agent.upload({
        file: testFile1,
        userId: 'test-user-1',
        category: 'general'
      });

      await agent.upload({
        file: testFile2,
        userId: 'test-user-1',
        category: 'aadhaar'
      });

      const aadhaarDocs = await agent.getDocuments('test-user-1', { category: 'aadhaar' });
      expect(aadhaarDocs).toHaveLength(1);
      expect(aadhaarDocs[0].category).toBe('aadhaar');
    });
  });

  describe('Document Search', () => {
    test('should search documents by filename', async () => {
      const testFile = path.join(testDir, 'searchable_document.pdf');
      fs.writeFileSync(testFile, Buffer.from('%PDF-1.1\nSearchable content\n%EOF\n'));

      await agent.upload({
        file: testFile,
        userId: 'test-user-1'
      });

      const results = await agent.searchDocuments('test-user-1', 'searchable');
      expect(results).toHaveLength(1);
      expect(results[0].originalName).toContain('searchable');
    });

    test('should search documents by category', async () => {
      const testFile = path.join(testDir, 'pan_card.pdf');
      fs.writeFileSync(testFile, Buffer.from('%PDF-1.1\nPAN card content\n%EOF\n'));

      await agent.upload({
        file: testFile,
        userId: 'test-user-1'
      });

      const results = await agent.searchDocuments('test-user-1', 'pan');
      expect(results).toHaveLength(1);
      expect(results[0].category).toBe('pan');
    });
  });

  describe('Document Deletion', () => {
    test('should delete document successfully', async () => {
      const testFile = path.join(testDir, 'delete.pdf');
      fs.writeFileSync(testFile, Buffer.from('%PDF-1.1\nDelete test content\n%EOF\n'));

      const uploaded = await agent.upload({
        file: testFile,
        userId: 'test-user-1'
      });

      await agent.deleteDocument(uploaded.id);

      const document = await agent.getDocumentById(uploaded.id);
      expect(document).toBeNull();
    });

    test('should fail to delete non-existent document', async () => {
      await expect(agent.deleteDocument('non-existent-id')).rejects.toThrow('Document not found');
    });
  });

  describe('Category Management', () => {
    test('should add custom category', async () => {
      const customRules = [/custom/i, /test/i];
      await agent.addCategory('custom', customRules);

      const categories = agent.getCategories();
      expect(categories).toContain('custom');
    });

    test('should remove category', async () => {
      await agent.removeCategory('general');

      const categories = agent.getCategories();
      expect(categories).not.toContain('general');
    });

    test('should use custom category for auto-categorization', async () => {
      const customRules = [/custom_doc/i];
      await agent.addCategory('custom', customRules);

      const testFile = path.join(testDir, 'custom_doc.pdf');
      fs.writeFileSync(testFile, Buffer.from('%PDF-1.1\nCustom document content\n%EOF\n'));

      const result = await agent.upload({
        file: testFile,
        userId: 'test-user-1'
      });

      expect(result.category).toBe('custom');
    });
  });

  describe('Security', () => {
    test('should encrypt documents', async () => {
      const testContent = '%PDF-1.1\nSensitive document content\n%EOF\n';
      const testFile = path.join(testDir, 'sensitive.pdf');
      fs.writeFileSync(testFile, testContent);

      const uploaded = await agent.upload({
        file: testFile,
        userId: 'test-user-1'
      });

      // Check that the stored file is encrypted (not readable as plain text)
      const encryptedFilePath = path.join(testDir, 'files', 'test-user-1', `${uploaded.id}.enc`);
      expect(fs.existsSync(encryptedFilePath)).toBe(true);

      const encryptedContent = fs.readFileSync(encryptedFilePath, 'utf8');
      expect(encryptedContent).not.toContain(testContent);
    });

    test('should isolate user data', async () => {
      const testFile1 = path.join(testDir, 'user1.pdf');
      const testFile2 = path.join(testDir, 'user2.pdf');
      
      fs.writeFileSync(testFile1, Buffer.from('%PDF-1.1\nUser 1 content\n%EOF\n'));
      fs.writeFileSync(testFile2, Buffer.from('%PDF-1.1\nUser 2 content\n%EOF\n'));

      await agent.upload({
        file: testFile1,
        userId: 'user-1'
      });

      await agent.upload({
        file: testFile2,
        userId: 'user-2'
      });

      const user1Docs = await agent.getDocuments('user-1');
      const user2Docs = await agent.getDocuments('user-2');

      expect(user1Docs).toHaveLength(1);
      expect(user2Docs).toHaveLength(1);
      expect(user1Docs[0].userId).toBe('user-1');
      expect(user2Docs[0].userId).toBe('user-2');
    });
  });
});