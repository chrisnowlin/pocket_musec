import * as fs from 'fs';
import * as path from 'path';
import { app } from 'electron';

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR'
}

class Logger {
  private logDir: string;
  private logFile: string;

  constructor() {
    this.logDir = path.join(app.getPath('userData'), 'logs');
    this.logFile = path.join(this.logDir, `pocketmusec-${this.getDateString()}.log`);
    this.ensureLogDirectory();
  }

  private ensureLogDirectory(): void {
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }
  }

  private getDateString(): string {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  }

  private getTimestamp(): string {
    const now = new Date();
    return now.toISOString();
  }

  private formatMessage(level: LogLevel, message: string, data?: any): string {
    const timestamp = this.getTimestamp();
    let logMessage = `[${timestamp}] [${level}] ${message}`;
    
    if (data) {
      if (data instanceof Error) {
        logMessage += `\n  Error: ${data.message}\n  Stack: ${data.stack}`;
      } else if (typeof data === 'object') {
        logMessage += `\n  Data: ${JSON.stringify(data, null, 2)}`;
      } else {
        logMessage += `\n  Data: ${data}`;
      }
    }
    
    return logMessage;
  }

  private writeLog(level: LogLevel, message: string, data?: any): void {
    const logMessage = this.formatMessage(level, message, data);
    
    // Write to file
    fs.appendFileSync(this.logFile, logMessage + '\n');
    
    // Also write to console
    switch (level) {
      case LogLevel.DEBUG:
      case LogLevel.INFO:
        console.log(logMessage);
        break;
      case LogLevel.WARN:
        console.warn(logMessage);
        break;
      case LogLevel.ERROR:
        console.error(logMessage);
        break;
    }
  }

  debug(message: string, data?: any): void {
    this.writeLog(LogLevel.DEBUG, message, data);
  }

  info(message: string, data?: any): void {
    this.writeLog(LogLevel.INFO, message, data);
  }

  warn(message: string, data?: any): void {
    this.writeLog(LogLevel.WARN, message, data);
  }

  error(message: string, data?: any): void {
    this.writeLog(LogLevel.ERROR, message, data);
  }

  getLogPath(): string {
    return this.logFile;
  }

  cleanOldLogs(daysToKeep: number = 7): void {
    try {
      const files = fs.readdirSync(this.logDir);
      const now = Date.now();
      const maxAge = daysToKeep * 24 * 60 * 60 * 1000;

      files.forEach(file => {
        if (file.startsWith('pocketmusec-') && file.endsWith('.log')) {
          const filePath = path.join(this.logDir, file);
          const stats = fs.statSync(filePath);
          const age = now - stats.mtime.getTime();

          if (age > maxAge) {
            fs.unlinkSync(filePath);
            this.info(`Deleted old log file: ${file}`);
          }
        }
      });
    } catch (error) {
      this.error('Failed to clean old logs', error);
    }
  }
}

export const logger = new Logger();