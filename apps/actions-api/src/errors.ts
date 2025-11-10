/**
 * Enhanced Error Handling System for Actions API
 * Provides structured, categorized errors with recovery suggestions
 */

import { ErrorCode, ApiError } from './types/index.js';

/**
 * Base error class for all API errors
 */
export class ApiException extends Error {
  public readonly code: ErrorCode;
  public readonly statusCode: number;
  public readonly details?: Record<string, any>;
  public readonly suggestions?: string[];

  constructor(
    code: ErrorCode,
    message: string,
    statusCode: number = 500,
    details?: Record<string, any>,
    suggestions?: string[]
  ) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
    this.suggestions = suggestions;
    Error.captureStackTrace(this, this.constructor);
  }

  public toJSON(): ApiError {
    return {
      code: this.code,
      message: this.message,
      details: this.details,
      suggestions: this.suggestions,
    };
  }
}

/**
 * Validation errors (400)
 */
export class ValidationError extends ApiException {
  constructor(message: string, details?: Record<string, any>) {
    super(ErrorCode.VALIDATION_ERROR, message, 400, details, [
      'Check the request parameters',
      'Ensure all required fields are provided',
      'Verify data types match the expected format',
    ]);
  }
}

/**
 * Authentication errors (401)
 */
export class AuthenticationError extends ApiException {
  constructor(message: string = 'Authentication required', details?: Record<string, any>) {
    super(ErrorCode.UNAUTHORIZED, message, 401, details, [
      'Provide a valid JWT token in the Authorization header',
      'Check if your token has expired',
      'Request a new token from the authentication service',
    ]);
  }
}

/**
 * Permission errors (403)
 */
export class PermissionError extends ApiException {
  constructor(message: string = 'Insufficient permissions', details?: Record<string, any>) {
    super(ErrorCode.FORBIDDEN, message, 403, details, [
      'Check if you have the required permissions for this operation',
      'Contact your administrator to request access',
      'Verify your role and capabilities',
    ]);
  }
}

/**
 * Not found errors (404)
 */
export class NotFoundError extends ApiException {
  constructor(resource: string, details?: Record<string, any>) {
    super(
      ErrorCode.NOT_FOUND,
      `Resource not found: ${resource}`,
      404,
      details,
      [
        'Verify the resource path or identifier',
        'Check if the resource exists',
        'Ensure you have access to the resource',
      ]
    );
  }
}

/**
 * Rate limiting errors (429)
 */
export class RateLimitError extends ApiException {
  constructor(retryAfter?: number, details?: Record<string, any>) {
    super(
      ErrorCode.RATE_LIMIT_EXCEEDED,
      'Rate limit exceeded',
      429,
      { ...details, retryAfter },
      [
        'Wait before making additional requests',
        `Retry after ${retryAfter || 60} seconds`,
        'Consider implementing exponential backoff',
      ]
    );
  }
}

/**
 * Command execution errors (500)
 */
export class CommandExecutionError extends ApiException {
  constructor(message: string, details?: Record<string, any>) {
    super(ErrorCode.COMMAND_EXECUTION_FAILED, message, 500, details, [
      'Check if the command is allowed',
      'Verify command syntax and arguments',
      'Check system permissions',
      'Review command output for error details',
    ]);
  }
}

/**
 * File operation errors (500)
 */
export class FileOperationError extends ApiException {
  constructor(operation: string, path: string, cause?: string, details?: Record<string, any>) {
    super(
      ErrorCode.FILE_OPERATION_FAILED,
      `File ${operation} failed: ${path}${cause ? ` - ${cause}` : ''}`,
      500,
      details,
      [
        'Check if the file or directory exists',
        'Verify you have the necessary permissions',
        'Ensure the path is valid and accessible',
        'Check for disk space if writing',
      ]
    );
  }
}

/**
 * Process operation errors (500)
 */
export class ProcessOperationError extends ApiException {
  constructor(operation: string, details?: Record<string, any>) {
    super(ErrorCode.PROCESS_OPERATION_FAILED, `Process ${operation} failed`, 500, details, [
      'Check if the process exists',
      'Verify you have permissions to manage the process',
      'Ensure the process name or PID is correct',
    ]);
  }
}

/**
 * Network errors (500)
 */
export class NetworkError extends ApiException {
  constructor(message: string, details?: Record<string, any>) {
    super(ErrorCode.NETWORK_ERROR, message, 500, details, [
      'Check your network connection',
      'Verify the remote host is accessible',
      'Check firewall settings',
      'Retry the operation',
    ]);
  }
}

/**
 * Timeout errors (500)
 */
export class TimeoutError extends ApiException {
  constructor(operation: string, timeout: number, details?: Record<string, any>) {
    super(
      ErrorCode.TIMEOUT,
      `Operation timed out after ${timeout}ms: ${operation}`,
      500,
      details,
      [
        'Increase the timeout value',
        'Check if the operation is resource-intensive',
        'Verify the system is not overloaded',
        'Try again later',
      ]
    );
  }
}

/**
 * Circuit breaker for external dependencies
 */
export class CircuitBreaker {
  private failures: number = 0;
  private lastFailureTime: number = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private readonly threshold: number = 5,
    private readonly timeout: number = 60000, // 1 minute
    private readonly resetTimeout: number = 30000 // 30 seconds
  ) {}

  public async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailureTime > this.resetTimeout) {
        this.state = 'half-open';
      } else {
        throw new ApiException(
          ErrorCode.INTERNAL_ERROR,
          'Circuit breaker is open - service temporarily unavailable',
          503,
          { state: this.state, failures: this.failures }
        );
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    this.state = 'closed';
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();

    if (this.failures >= this.threshold) {
      this.state = 'open';
    }
  }

  public getState(): { state: string; failures: number } {
    return {
      state: this.state,
      failures: this.failures,
    };
  }
}

/**
 * Retry logic for transient failures
 */
export async function retryOperation<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delayMs: number = 1000,
  backoff: number = 2
): Promise<T> {
  let lastError: Error;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (attempt < maxRetries) {
        const delay = delayMs * Math.pow(backoff, attempt);
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
  }

  throw new ApiException(
    ErrorCode.INTERNAL_ERROR,
    `Operation failed after ${maxRetries + 1} attempts: ${lastError!.message}`,
    500,
    { lastError: lastError!.message }
  );
}

/**
 * Convert unknown errors to ApiException
 */
export function normalizeError(error: unknown): ApiException {
  if (error instanceof ApiException) {
    return error;
  }

  if (error instanceof Error) {
    return new ApiException(ErrorCode.INTERNAL_ERROR, error.message, 500, {
      originalError: error.name,
      stack: error.stack,
    });
  }

  return new ApiException(
    ErrorCode.INTERNAL_ERROR,
    'An unknown error occurred',
    500,
    { error: String(error) }
  );
}
