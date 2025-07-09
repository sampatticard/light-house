# DocumentAgent - Secure Document Upload & Storage Library

A robust, secure, and reusable TypeScript library for document upload, storage, and management in Electron applications.

## Features

- 🔒 **Secure Storage**: AES-256 encryption for all documents
- 📁 **Auto-Categorization**: Intelligent document classification
- 🔍 **OCR Integration**: Optional text extraction from images and PDFs
- 📊 **SQLite Database**: Efficient metadata storage and search
- 🛡️ **User Isolation**: Complete data separation between users
- 🧩 **Extensible**: Plugin-based architecture for custom storage engines
- 📝 **TypeScript**: Full type safety and IntelliSense support

## Installation

```bash
npm install document-agent
```

## Quick Start

```typescript
import { DocumentAgent } from 'document-agent';

// Initialize the agent
const agent = new DocumentAgent({
  storagePath: './user_data',
  encryptionKey: process.env.ENCRYPTION_KEY, // Optional - auto-generated if not provided
  enableOCR: true,
  maxFileSize: 10 * 1024 * 1024, // 10MB
  logLevel: 'info'
});

// Upload a document
const document = await agent.upload({
  file: '/path/to/document.pdf',
  userId: 'user_123',
  category: 'aadhaar' // Optional - auto-detected if not provided
});

// Retrieve documents
const documents = await agent.getDocuments('user_123', {
  category: 'aadhaar',
  limit: 10
});

// Search documents
const results = await agent.searchDocuments('user_123', 'aadhaar');

// Get document data
const fileData = await agent.getDocumentData(document.id);

// Clean up
await agent.cleanup();
```

## API Reference

### Constructor Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `storagePath` | `string` | **Required** | Base directory for storage |
| `encryptionKey` | `string` | Auto-generated | 64-character hex encryption key |
| `enableOCR` | `boolean` | `false` | Enable OCR text extraction |
| `maxFileSize` | `number` | `10MB` | Maximum file size in bytes |
| `supportedFormats` | `string[]` | `['pdf', 'jpg', 'jpeg', 'png', 'docx']` | Supported file formats |
| `logLevel` | `string` | `'info'` | Log level (error, warn, info, debug) |

### Methods

#### `upload(options: UploadOptions): Promise<DocumentRecord>`

Upload and encrypt a document.

```typescript
const document = await agent.upload({
  file: '/path/to/file.pdf', // File path or Buffer
  userId: 'user_123',
  category: 'pan', // Optional
  metadata: { source: 'mobile_app' }, // Optional
  enableOCR: true // Optional, overrides global setting
});
```

#### `getDocuments(userId: string, options?: SearchOptions): Promise<DocumentRecord[]>`

Retrieve user documents with optional filtering.

```typescript
const documents = await agent.getDocuments('user_123', {
  category: 'aadhaar',
  fileType: 'pdf',
  dateRange: {
    start: new Date('2023-01-01'),
    end: new Date('2023-12-31')
  },
  limit: 20,
  offset: 0
});
```

#### `searchDocuments(userId: string, searchTerm: string): Promise<DocumentRecord[]>`

Full-text search across document names, categories, and OCR text.

```typescript
const results = await agent.searchDocuments('user_123', 'passport');
```

#### `getDocumentData(documentId: string): Promise<Buffer>`

Retrieve and decrypt document file data.

```typescript
const fileBuffer = await agent.getDocumentData(documentId);
fs.writeFileSync('decrypted_file.pdf', fileBuffer);
```

#### `deleteDocument(documentId: string): Promise<void>`

Permanently delete a document and its encrypted file.

```typescript
await agent.deleteDocument(documentId);
```

### Category Management

#### `addCategory(name: string, rules: RegExp[]): Promise<void>`

Add custom categorization rules.

```typescript
await agent.addCategory('insurance', [
  /insurance/i,
  /policy/i,
  /premium/i
]);
```

#### `removeCategory(name: string): Promise<void>`

Remove a category.

```typescript
await agent.removeCategory('general');
```

#### `getCategories(): string[]`

Get all available categories.

```typescript
const categories = agent.getCategories();
console.log(categories); // ['aadhaar', 'pan', 'bank_statement', ...]
```

## Built-in Categories

The library includes intelligent auto-categorization for common Indian documents:

- **aadhaar**: Aadhaar cards and UID documents
- **pan**: PAN cards and tax documents
- **bank_statement**: Bank statements and transaction history
- **passport**: Passport and travel documents
- **driving_license**: Driving licenses
- **voter_id**: Voter ID cards
- **insurance**: Insurance policies and documents
- **tax_document**: Tax returns and related documents
- **general**: Fallback category for unclassified documents

## Security Features

- **AES-256 Encryption**: All documents encrypted at rest
- **Key Management**: Secure key generation and rotation support
- **User Isolation**: Complete data separation between users
- **Hash Verification**: SHA-256 hashes for integrity checking
- **No Cloud Dependencies**: All processing happens locally

## OCR Integration

Enable OCR to extract text from images and PDFs:

```typescript
const agent = new DocumentAgent({
  storagePath: './data',
  enableOCR: true
});

const document = await agent.upload({
  file: 'scanned_document.jpg',
  userId: 'user_123'
});

console.log(document.ocrText); // Extracted text content
```

## Testing

Run the test suite:

```bash
npm test
```