import * as crypto from 'crypto';
import * as forge from 'node-forge';

export class Encryptor {
  private key: Buffer;
  private algorithm = 'aes-256-gcm';

  constructor(encryptionKey?: string) {
    if (encryptionKey) {
      this.key = Buffer.from(encryptionKey, 'hex');
    } else {
      this.key = crypto.randomBytes(32);
    }
  }

encrypt(data: Buffer): { encrypted: Buffer; iv: Buffer; tag: Buffer } {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(this.algorithm, this.key, iv) as crypto.CipherGCM;
    cipher.setAAD(Buffer.from('DocumentAgent'));

    const encrypted = Buffer.concat([
      cipher.update(data),
      cipher.final()
    ]);

    const tag = cipher.getAuthTag();

    return { encrypted, iv, tag };
  }

  decrypt(encryptedData: Buffer, iv: Buffer, tag: Buffer): Buffer {
    const decipher = crypto.createDecipheriv(this.algorithm, this.key, iv) as crypto.DecipherGCM;
    decipher.setAAD(Buffer.from('DocumentAgent'));
    decipher.setAuthTag(tag);

    return Buffer.concat([
      decipher.update(encryptedData),
      decipher.final()
    ]);
  }

  encryptMetadata(metadata: Record<string, any>): string {
    const jsonString = JSON.stringify(metadata);
    const { encrypted, iv, tag } = this.encrypt(Buffer.from(jsonString));
    
    return JSON.stringify({
      encrypted: encrypted.toString('hex'),
      iv: iv.toString('hex'),
      tag: tag.toString('hex')
    });
  }

  decryptMetadata(encryptedMetadata: string): Record<string, any> {
    const parsed = JSON.parse(encryptedMetadata);
    const decrypted = this.decrypt(
      Buffer.from(parsed.encrypted, 'hex'),
      Buffer.from(parsed.iv, 'hex'),
      Buffer.from(parsed.tag, 'hex')
    );
    
    return JSON.parse(decrypted.toString());
  }

  getKeyHex(): string {
    return this.key.toString('hex');
  }

  generateHash(data: Buffer): string {
    return crypto.createHash('sha256').update(data).digest('hex');
  }
}
