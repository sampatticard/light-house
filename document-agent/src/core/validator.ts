import fileType from 'file-type';
import * as fs from 'fs';
import * as path from 'path';

export class Validator {
  private supportedFormats: string[];
  private maxFileSize: number;

  constructor(supportedFormats: string[] = ['pdf', 'jpg', 'jpeg', 'png', 'docx'], maxFileSize: number = 10 * 1024 * 1024) {
    this.supportedFormats = supportedFormats;
    this.maxFileSize = maxFileSize;
  }

  async validateFile(filePath: string): Promise<{ isValid: boolean; error?: string; fileType?: string }> {
    try {
      // Check if file exists
      if (!fs.existsSync(filePath)) {
        return { isValid: false, error: 'File does not exist' };
      }

      // Check file size
      const stats = fs.statSync(filePath);
      if (stats.size > this.maxFileSize) {
        return { isValid: false, error: `File size exceeds limit of ${this.maxFileSize} bytes` };
      }

      // Check file type
      const buffer = fs.readFileSync(filePath);
      const detectedType = await fileType.fromBuffer(buffer);
      
      if (!detectedType) {
        return { isValid: false, error: 'Unable to determine file type' };
      }

      if (!this.supportedFormats.includes(detectedType.ext)) {
        return { isValid: false, error: `Unsupported file format: ${detectedType.ext}` };
      }

      return { isValid: true, fileType: detectedType.ext };
    } catch (error) {
      if (error instanceof Error) {
        return { isValid: false, error: `Validation error: ${error.message}` };
      }
      return { isValid: false, error: 'Validation error: Unknown error' };
    }
  }

  async validateBuffer(buffer: Buffer, originalName: string): Promise<{ isValid: boolean; error?: string; fileType?: string }> {
    try {
      // Check buffer size
      if (buffer.length > this.maxFileSize) {
        return { isValid: false, error: `File size exceeds limit of ${this.maxFileSize} bytes` };
      }

      // Check file type
      const detectedType = await fileType.fromBuffer(buffer);
      
      if (!detectedType) {
        // Fallback to extension check
        const ext = path.extname(originalName).toLowerCase().substring(1);
        if (!this.supportedFormats.includes(ext)) {
          return { isValid: false, error: 'Unable to determine file type' };
        }
        return { isValid: true, fileType: ext };
      }

      if (!this.supportedFormats.includes(detectedType.ext)) {
        return { isValid: false, error: `Unsupported file format: ${detectedType.ext}` };
      }

      return { isValid: true, fileType: detectedType.ext };
    } catch (error) {
      if (error instanceof Error) {
        return { isValid: false, error: `Validation error: ${error.message}` };
      }
      return { isValid: false, error: 'Validation error: Unknown error' };
    }
  }
}