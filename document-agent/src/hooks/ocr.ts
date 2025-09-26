import { createWorker } from 'tesseract.js';

export class OCRProcessor {
  private worker: any;
  private isInitialized = false;

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    this.worker = await createWorker();
    await this.worker.loadLanguage('eng');
    await this.worker.initialize('eng');
    this.isInitialized = true;
  }

  async processDocument(buffer: Buffer, fileType: string): Promise<string> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    try {
      const { data: { text } } = await this.worker.recognize(buffer);
      return text.trim();
    } catch (error) {
      console.error('OCR processing failed:', error);
      return '';
    }
  }

  async terminate(): Promise<void> {
    if (this.worker) {
      await this.worker.terminate();
      this.isInitialized = false;
    }
  }
}