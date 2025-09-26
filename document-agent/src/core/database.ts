import * as sqlite3 from 'sqlite3';
import * as path from 'path';
import { DocumentRecord, SearchOptions } from '../types';

export class Database {
  private db: sqlite3.Database;

  constructor(dbPath: string) {
    try {
      // Make sure we're using a fully resolved absolute path
      const absolutePath = path.resolve(dbPath);
      
      // Ensure the directory for the database exists
      const dbDir = path.dirname(absolutePath);
      const fs = require('fs');
      if (!fs.existsSync(dbDir)) {
        fs.mkdirSync(dbDir, { recursive: true });
      }
      
      // Open the database with additional flags for better reliability
      // Using verbose mode for better error messages
      const sqlite3Verbose = sqlite3.verbose();
      this.db = new sqlite3Verbose.Database(absolutePath, sqlite3.OPEN_READWRITE | sqlite3.OPEN_CREATE);
      
      // Improve database reliability by setting some pragmas
      this.db.serialize(() => {
        this.db.run('PRAGMA journal_mode = WAL;');
        this.db.run('PRAGMA busy_timeout = 5000;');
        this.db.run('PRAGMA synchronous = NORMAL;');
        this.initializeDatabase();
      });
    } catch (err) {
      console.error(`Database initialization error: ${err instanceof Error ? err.message : String(err)}`);
      console.error(`Attempted database path: ${dbPath}`);
      throw err;
    }
  }

  private initializeDatabase(): void {
    const createTableQuery = `
      CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        userId TEXT NOT NULL,
        originalName TEXT NOT NULL,
        category TEXT NOT NULL,
        fileType TEXT NOT NULL,
        size INTEGER NOT NULL,
        hash TEXT NOT NULL,
        encryptedPath TEXT NOT NULL,
        metadata TEXT,
        ocrText TEXT,
        createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
        updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
      );
      
      CREATE INDEX IF NOT EXISTS idx_user_id ON documents(userId);
      CREATE INDEX IF NOT EXISTS idx_category ON documents(category);
      CREATE INDEX IF NOT EXISTS idx_file_type ON documents(fileType);
      CREATE INDEX IF NOT EXISTS idx_hash ON documents(hash);
    `;

    this.db.exec(createTableQuery);
  }

  async insertDocument(doc: Omit<DocumentRecord, 'createdAt' | 'updatedAt'>): Promise<void> {
    return new Promise((resolve, reject) => {
      const query = `
        INSERT INTO documents (id, userId, originalName, category, fileType, size, hash, encryptedPath, metadata, ocrText)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `;
      
      this.db.run(query, [
        doc.id,
        doc.userId,
        doc.originalName,
        doc.category,
        doc.fileType,
        doc.size,
        doc.hash,
        doc.encryptedPath,
        JSON.stringify(doc.metadata || {}),
        doc.ocrText || null
      ], (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  async getDocuments(userId: string, options: SearchOptions = {}): Promise<DocumentRecord[]> {
    return new Promise((resolve, reject) => {
      let query = 'SELECT * FROM documents WHERE userId = ?';
      const params: any[] = [userId];

      if (options.category) {
        query += ' AND category = ?';
        params.push(options.category);
      }

      if (options.fileType) {
        query += ' AND fileType = ?';
        params.push(options.fileType);
      }

      if (options.dateRange) {
        query += ' AND createdAt BETWEEN ? AND ?';
        params.push(options.dateRange.start.toISOString(), options.dateRange.end.toISOString());
      }

      query += ' ORDER BY createdAt DESC';

      if (options.limit) {
        query += ' LIMIT ?';
        params.push(options.limit);
      }

      if (options.offset) {
        query += ' OFFSET ?';
        params.push(options.offset);
      }

      this.db.all(query, params, (err, rows: any[]) => {
        if (err) {
          reject(err);
        } else {
          const documents: DocumentRecord[] = rows.map(row => ({
            ...row,
            metadata: JSON.parse(row.metadata || '{}'),
            createdAt: new Date(row.createdAt),
            updatedAt: new Date(row.updatedAt)
          }));
          resolve(documents);
        }
      });
    });
  }

  async getDocumentById(id: string): Promise<DocumentRecord | null> {
    return new Promise((resolve, reject) => {
      const query = 'SELECT * FROM documents WHERE id = ?';
      
      this.db.get(query, [id], (err, row: any) => {
        if (err) {
          reject(err);
        } else if (row) {
          const document: DocumentRecord = {
            ...row,
            metadata: JSON.parse(row.metadata || '{}'),
            createdAt: new Date(row.createdAt),
            updatedAt: new Date(row.updatedAt)
          };
          resolve(document);
        } else {
          resolve(null);
        }
      });
    });
  }

  async updateDocument(id: string, updates: Partial<DocumentRecord>): Promise<void> {
    return new Promise((resolve, reject) => {
      const fields = Object.keys(updates).filter(key => key !== 'id');
      const setClause = fields.map(field => `${field} = ?`).join(', ');
      const values = fields.map(field => {
        if (field === 'metadata') {
          return JSON.stringify(updates[field as keyof DocumentRecord]);
        }
        return updates[field as keyof DocumentRecord];
      });

      const query = `UPDATE documents SET ${setClause}, updatedAt = CURRENT_TIMESTAMP WHERE id = ?`;
      values.push(id);

      this.db.run(query, values, (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  async deleteDocument(id: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const query = 'DELETE FROM documents WHERE id = ?';
      
      this.db.run(query, [id], (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  async searchDocuments(userId: string, searchTerm: string): Promise<DocumentRecord[]> {
    return new Promise((resolve, reject) => {
      const query = `
        SELECT * FROM documents 
        WHERE userId = ? AND (
          originalName LIKE ? OR 
          category LIKE ? OR 
          ocrText LIKE ? OR
          metadata LIKE ?
        )
        ORDER BY createdAt DESC
      `;
      
      const searchPattern = `%${searchTerm}%`;
      
      this.db.all(query, [userId, searchPattern, searchPattern, searchPattern, searchPattern], (err, rows: any[]) => {
        if (err) {
          reject(err);
        } else {
          const documents: DocumentRecord[] = rows.map(row => ({
            ...row,
            metadata: JSON.parse(row.metadata || '{}'),
            createdAt: new Date(row.createdAt),
            updatedAt: new Date(row.updatedAt)
          }));
          resolve(documents);
        }
      });
    });
  }

  close(): void {
    try {
      if (this.db) {
        this.db.close();
      }
    } catch (err) {
      console.error(`Error closing database: ${err instanceof Error ? err.message : String(err)}`);
      // Don't rethrow as we want cleanup to continue even if there's an error
    }
  }
}