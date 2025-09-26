import { DocumentAgent, DocumentAgentConfig, UploadOptions } from './src';
import * as fs from 'fs';
import * as path from 'path';

async function main() {
  // 1. Initialize DocumentAgent
  const storagePath = path.join(__dirname, 'example-storage');
  if (!fs.existsSync(storagePath)) fs.mkdirSync(storagePath, { recursive: true });

  const config: DocumentAgentConfig = {
    storagePath,
    encryptionKey: 'a'.repeat(64), // 32 bytes in hex
    enableOCR: false,
    logLevel: 'info',
    maxFileSize: 5 * 1024 * 1024, // 5MB
  };
  const agent = new DocumentAgent(config);

  // 2. Add a custom category
  await agent.addCategory('custom', [/(custom)/i]);
  console.log('Categories:', agent.getCategories());

  // 3. Upload a document
  const testFile = path.join(__dirname, 'test.pdf');
  fs.writeFileSync(testFile, Buffer.from('%PDF-1.1\n%EOF\n'));
  const uploadOptions: UploadOptions = {
    file: testFile,
    userId: 'user-1',
    category: 'custom',
  };
  const doc = await agent.upload(uploadOptions);
  console.log('Uploaded document:', doc);

  // 4. List documents for user
  const docs = await agent.getDocuments('user-1');
  console.log('Documents for user-1:', docs);

  // 5. Retrieve document by ID
  const docById = await agent.getDocumentById(doc.id);
  console.log('Document by ID:', docById);

  // 6. Retrieve document data
  const data = await agent.getDocumentData(doc.id);
  console.log('Document data (as string):', data.toString());

  // 7. Search documents
  const searchResults = await agent.searchDocuments('user-1', 'Test');
  console.log('Search results:', searchResults);

  // 8. Remove category
  await agent.removeCategory('custom');
  console.log('Categories after removal:', agent.getCategories());

  // 9. Delete document
  await agent.deleteDocument(doc.id);
  console.log('Document deleted.');

  // 10. Cleanup
  await agent.cleanup();
  fs.rmSync(storagePath, { recursive: true, force: true });
  fs.unlinkSync(testFile);
  console.log('Cleanup done.');
}

main().catch(err => {
  console.error('Error in example app:', err);
});
