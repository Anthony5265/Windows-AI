/**
 * Audit Logging Middleware for Actions API
 * Records all system operations for security and compliance
 */

import { Request, Response, NextFunction } from 'express';
import { writeFile, appendFile } from 'fs/promises';
import { join } from 'path';
import { AuditLogEntry } from '../types/index.js';
import { ApiException } from '../errors.js';

// =====================================================================
// Audit Logger
// =====================================================================

export class AuditLogger {
  private logFile: string;
  private buffer: AuditLogEntry[] = [];
  private flushInterval: NodeJS.Timeout;

  constructor(logPath: string = './logs/security.log', flushIntervalMs: number = 5000) {
    this.logFile = logPath;

    // Flush buffer periodically
    this.flushInterval = setInterval(() => {
      this.flush().catch((err) => console.error('Failed to flush audit log:', err));
    }, flushIntervalMs);
  }

  /**
   * Log an audit entry
   */
  public log(entry: Omit<AuditLogEntry, 'timestamp'>): void {
    const fullEntry: AuditLogEntry = {
      ...entry,
      timestamp: new Date(),
    };

    this.buffer.push(fullEntry);

    // Also log to console for immediate visibility
    console.log(JSON.stringify(fullEntry));

    // Flush immediately for security-critical events
    if (entry.level === 'security' || entry.level === 'error') {
      this.flush().catch((err) => console.error('Failed to flush security log:', err));
    }
  }

  /**
   * Flush buffer to disk
   */
  private async flush(): Promise<void> {
    if (this.buffer.length === 0) return;

    const entries = [...this.buffer];
    this.buffer = [];

    const lines = entries.map((entry) => JSON.stringify(entry) + '\n').join('');

    try {
      await appendFile(this.logFile, lines, 'utf8');
    } catch (error) {
      // If file doesn't exist, try to create it
      console.error('Audit log write failed, attempting to create file:', error);
    }
  }

  /**
   * Cleanup on shutdown
   */
  public async close(): Promise<void> {
    clearInterval(this.flushInterval);
    await this.flush();
  }
}

// Global audit logger instance
const auditLogger = new AuditLogger();

// =====================================================================
// Audit Middleware
// =====================================================================

/**
 * Audit logging middleware - logs all requests and responses
 */
export function auditLog(req: Request, res: Response, next: NextFunction): void {
  const startTime = Date.now();
  const user = (req as any).user;

  // Capture original send function
  const originalSend = res.send.bind(res);

  // Override send to capture response
  res.send = function (body: any): Response {
    const duration = Date.now() - startTime;
    const statusCode = res.statusCode;

    // Determine log level
    let level: 'info' | 'warn' | 'error' | 'security' = 'info';
    if (statusCode >= 500) {
      level = 'error';
    } else if (statusCode >= 400) {
      level = 'warn';
    } else if (req.path.includes('/auth') || req.path.includes('/login')) {
      level = 'security';
    }

    // Parse response body if it's an error
    let errorInfo: { code: any; message: string } | undefined;
    if (statusCode >= 400 && body) {
      try {
        const parsed = typeof body === 'string' ? JSON.parse(body) : body;
        if (parsed.error) {
          errorInfo = {
            code: parsed.error.code,
            message: parsed.error.message,
          };
        }
      } catch (e) {
        // Ignore parse errors
      }
    }

    // Log the entry
    auditLogger.log({
      level,
      action: `${req.method} ${req.path}`,
      userId: user?.sub,
      clientIp: req.ip,
      request: {
        method: req.method,
        path: req.path,
        body: req.body && Object.keys(req.body).length > 0 ? sanitizeRequestBody(req.body) : undefined,
      },
      response: {
        status: statusCode,
        duration,
      },
      error: errorInfo,
      metadata: {
        userAgent: req.headers['user-agent'],
        referer: req.headers.referer,
      },
    });

    return originalSend(body);
  };

  next();
}

/**
 * Sanitize request body for logging (remove sensitive data)
 */
function sanitizeRequestBody(body: any): any {
  const sensitiveFields = ['password', 'token', 'secret', 'apiKey', 'api_key', 'authorization'];
  const sanitized = { ...body };

  for (const field of sensitiveFields) {
    if (field in sanitized) {
      sanitized[field] = '[REDACTED]';
    }
  }

  return sanitized;
}

/**
 * Log a security event (authentication, authorization, etc.)
 */
export function logSecurityEvent(
  action: string,
  userId?: string,
  success: boolean = true,
  metadata?: Record<string, any>
): void {
  auditLogger.log({
    level: 'security',
    action,
    userId,
    metadata: {
      ...metadata,
      success,
    },
  });
}

/**
 * Log a command execution
 */
export function logCommandExecution(
  command: string,
  userId?: string,
  success: boolean = true,
  metadata?: Record<string, any>
): void {
  auditLogger.log({
    level: success ? 'info' : 'error',
    action: `COMMAND: ${command}`,
    userId,
    metadata,
  });
}

/**
 * Log a file operation
 */
export function logFileOperation(
  operation: string,
  path: string,
  userId?: string,
  success: boolean = true,
  metadata?: Record<string, any>
): void {
  auditLogger.log({
    level: success ? 'info' : 'error',
    action: `FILE_${operation.toUpperCase()}: ${path}`,
    userId,
    metadata,
  });
}

/**
 * Log a process operation
 */
export function logProcessOperation(
  operation: string,
  target: string | number,
  userId?: string,
  success: boolean = true,
  metadata?: Record<string, any>
): void {
  auditLogger.log({
    level: success ? 'info' : 'warn',
    action: `PROCESS_${operation.toUpperCase()}: ${target}`,
    userId,
    metadata,
  });
}

/**
 * Export audit logger for graceful shutdown
 */
export { auditLogger };
