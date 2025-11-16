import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import axios from 'axios';
import findFreePort from 'find-free-port';
import { logger } from './logger';
import { app } from 'electron';

export interface BackendStatus {
  isRunning: boolean;
  port?: number;
  pid?: number;
  error?: string;
}

export class BackendManager {
  private process: ChildProcess | null = null;
  private port: number = 0;
  private isStarting: boolean = false;
  private startupTimeout: NodeJS.Timeout | null = null;
  private healthCheckInterval: NodeJS.Timeout | null = null;

  constructor() {
    // Handle process cleanup on exit
    process.on('exit', () => this.stop());
    process.on('SIGINT', () => this.stop());
    process.on('SIGTERM', () => this.stop());
  }

  /**
   * Start the Python backend server
   */
  async start(): Promise<number> {
    if (this.isStarting) {
      logger.warn('Backend start requested but already starting');
      throw new Error('Backend is already starting');
    }

    if (this.process && !this.process.killed) {
      logger.info(`Backend already running on port ${this.port}`);
      return this.port;
    }

    this.isStarting = true;
    logger.info('Starting backend process');

    try {
      // Find available port
      this.port = await this.findAvailablePort();
      logger.info(`Found available port: ${this.port}`);
      
      // Start the backend process
      await this.startBackendProcess();
      logger.info('Backend process spawned, waiting for health check');
      
      // Wait for backend to be healthy
      await this.waitForHealthy();
      logger.info('Backend health check passed');
      
      // Start health check monitoring
      this.startHealthCheckMonitoring();
      logger.info('Backend health monitoring started');
      
      logger.info(`Backend started successfully on port ${this.port}`);
      return this.port;
      
    } catch (error) {
      this.isStarting = false;
      logger.error('Failed to start backend', error);
      await this.stop();
      throw error;
    }
  }

  /**
   * Stop the Python backend server
   */
  async stop(): Promise<void> {
    this.isStarting = false;
    
    // Clear health check interval
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }

    // Clear startup timeout
    if (this.startupTimeout) {
      clearTimeout(this.startupTimeout);
      this.startupTimeout = null;
    }

    if (this.process && !this.process.killed) {
      try {
        // Try graceful shutdown first
        await axios.post(`http://localhost:${this.port}/api/shutdown`, {
          timeout: 5000
        });
        
        // Wait a bit for graceful shutdown
        await new Promise(resolve => setTimeout(resolve, 2000));
        
      } catch (error) {
        console.warn('Graceful shutdown failed, forcing termination:', error);
      }

      // Force kill if still running
      if (this.process && !this.process.killed) {
        this.process.kill('SIGTERM');
        
        // Wait a bit and force kill if needed
        setTimeout(() => {
          if (this.process && !this.process.killed) {
            this.process.kill('SIGKILL');
          }
        }, 3000);
      }
    }

    this.process = null;
    this.port = 0;
    console.log('Backend stopped');
  }

  /**
   * Get current backend status
   */
  getStatus(): BackendStatus {
    return {
      isRunning: this.process !== null && !this.process.killed,
      port: this.port || undefined,
      pid: this.process?.pid,
      error: undefined
    };
  }

  /**
   * Restart the backend
   */
  async restart(): Promise<number> {
    await this.stop();
    return this.start();
  }

  /**
   * Find an available port in the range 8000-9000
   */
  private async findAvailablePort(): Promise<number> {
    return new Promise((resolve, reject) => {
      findFreePort(8000, 9000, '127.0.0.1', (err: any, port: number) => {
        if (err) {
          reject(new Error(`Failed to find available port: ${err.message}`));
        } else {
          resolve(port);
        }
      });
    });
  }

  /**
   * Start the Python backend process
   */
  private async startBackendProcess(): Promise<void> {
    const isDev = !app.isPackaged;
    
    // Determine the backend executable path
    let backendPath: string;
    
    if (isDev) {
      // In development, use the Python script directly
      backendPath = path.join(__dirname, '../../run_api.py');
    } else {
      // In production, use the PyInstaller executable
      const resourcesPath = process.resourcesPath || path.join(__dirname, '../resources');
      backendPath = path.join(resourcesPath, 'backend', process.platform === 'win32' ? 'pocketmusec-backend.exe' : 'pocketmusec-backend');
    }

    // Verify backend exists
    if (!fs.existsSync(backendPath) && isDev) {
      throw new Error(`Backend script not found: ${backendPath}. Make sure you're running from the project root.`);
    } else if (!fs.existsSync(backendPath)) {
      throw new Error(`Backend executable not found: ${backendPath}`);
    }

    // Spawn the backend process
    let command: string;
    let commandArgs: string[];
    
    if (isDev) {
      command = 'python';
      commandArgs = [backendPath, `--port=${this.port}`, '--electron-mode'];
    } else {
      command = backendPath;
      commandArgs = [`--port=${this.port}`, '--electron-mode'];
    }

    this.process = spawn(command, commandArgs, {
      env: {
        ...process.env,
        ELECTRON_MODE: 'true',
        PORT: this.port.toString()
      },
      stdio: ['pipe', 'pipe', 'pipe']
    });

    // Handle process output
    if (this.process.stdout) {
      this.process.stdout.on('data', (data) => {
        const output = data.toString().trim();
        logger.debug(`Backend stdout: ${output}`);
      });
    }

    if (this.process.stderr) {
      this.process.stderr.on('data', (data) => {
        const output = data.toString().trim();
        // Log as debug since stderr often contains info logs from uvicorn
        logger.debug(`Backend stderr: ${output}`);
      });
    }

    // Handle process exit
    this.process.on('exit', (code, signal) => {
      logger.warn(`Backend process exited with code ${code}, signal ${signal}`);
      this.process = null;
      this.port = 0;
      
      // Clear health check interval
      if (this.healthCheckInterval) {
        clearInterval(this.healthCheckInterval);
        this.healthCheckInterval = null;
      }
    });

    // Handle process error
    this.process.on('error', (error) => {
      logger.error('Backend process error', error);
      this.process = null;
      this.port = 0;
    });
  }

  /**
   * Wait for the backend to become healthy
   */
  private async waitForHealthy(): Promise<void> {
    const maxAttempts = 30; // 30 seconds max
    let attempts = 0;

    return new Promise((resolve, reject) => {
      const checkHealth = async () => {
        attempts++;
        
        try {
          const response = await axios.get(`http://localhost:${this.port}/health`, {
            timeout: 2000
          });
          
          if (response.status === 200) {
            this.isStarting = false;
            resolve();
            return;
          }
        } catch (error) {
          // Backend not ready yet
        }

        if (attempts >= maxAttempts) {
          this.isStarting = false;
          reject(new Error('Backend failed to start within timeout period'));
          return;
        }

        // Check again in 1 second
        this.startupTimeout = setTimeout(checkHealth, 1000);
      };

      checkHealth();
    });
  }

  /**
   * Start monitoring backend health
   */
  private startHealthCheckMonitoring(): void {
    this.healthCheckInterval = setInterval(async () => {
      if (!this.process || this.process.killed) {
        return;
      }

      try {
        const response = await axios.get(`http://localhost:${this.port}/health`, {
          timeout: 5000
        });
        
        if (response.status !== 200) {
          console.warn('Backend health check failed, attempting restart');
          await this.restart();
        }
      } catch (error) {
        console.warn('Backend health check failed, attempting restart:', error);
        await this.restart();
      }
    }, 30000); // Check every 30 seconds
  }
}