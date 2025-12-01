/**
 * Security Middleware for Actions API
 * Provides authentication, authorization, rate limiting, and input validation
 */

import { Request, Response, NextFunction } from 'express';
import {
  AuthenticationError,
  PermissionError,
  RateLimitError,
  ValidationError,
  ApiException,
  normalizeError,
} from '../errors.js';
import { Permission, JWTPayload, RateLimitInfo } from '../types/index.js';
import crypto from 'crypto';

// =====================================================================
// JWT Authentication
// =====================================================================

const JWT_SECRET = process.env.JWT_SECRET || 'default-secret-change-in-production';
const JWT_ALGORITHM = 'HS256';

/**
 * Simple JWT implementation for internal authentication
 */
export class JWTAuth {
  /**
   * Create a JWT token
   */
  public static sign(payload: JWTPayload, expiresIn: number = 3600): string {
    const header = {
      alg: JWT_ALGORITHM,
      typ: 'JWT',
    };

    const now = Math.floor(Date.now() / 1000);
    const fullPayload = {
      ...payload,
      iat: payload.iat || now,
      exp: payload.exp || now + expiresIn,
    };

    const encodedHeader = this.base64urlEncode(JSON.stringify(header));
    const encodedPayload = this.base64urlEncode(JSON.stringify(fullPayload));
    const signature = this.sign256(`${encodedHeader}.${encodedPayload}`);

    return `${encodedHeader}.${encodedPayload}.${signature}`;
  }

  /**
   * Verify and decode a JWT token
   */
  public static verify(token: string): JWTPayload {
    const parts = token.split('.');
    if (parts.length !== 3) {
      throw new AuthenticationError('Invalid token format');
    }

    const [encodedHeader, encodedPayload, signature] = parts;

    // Verify signature
    const expectedSignature = this.sign256(`${encodedHeader}.${encodedPayload}`);
    if (signature !== expectedSignature) {
      throw new AuthenticationError('Invalid token signature');
    }

    // Decode payload
    const payload = JSON.parse(this.base64urlDecode(encodedPayload)) as JWTPayload;

    // Check expiration
    const now = Math.floor(Date.now() / 1000);
    if (payload.exp && payload.exp < now) {
      throw new AuthenticationError('Token expired');
    }

    return payload;
  }

  private static base64urlEncode(str: string): string {
    return Buffer.from(str)
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }

  private static base64urlDecode(str: string): string {
    str += '='.repeat((4 - (str.length % 4)) % 4);
    return Buffer.from(str.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString();
  }

  private static sign256(data: string): string {
    return crypto
      .createHmac('sha256', JWT_SECRET)
      .update(data)
      .digest('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }
}

/**
 * Authentication middleware - validates JWT token
 */
export function authenticate(req: Request, res: Response, next: NextFunction): void {
  try {
    // Extract token from Authorization header
    const authHeader = req.headers.authorization;
    if (!authHeader) {
      throw new AuthenticationError('No authorization header provided');
    }

    const [scheme, token] = authHeader.split(' ');
    if (scheme !== 'Bearer' || !token) {
      throw new AuthenticationError('Invalid authorization format. Use: Bearer <token>');
    }

    // Verify token
    const payload = JWTAuth.verify(token);

    // Attach user info to request
    (req as any).user = payload;

    next();
  } catch (error) {
    const apiError = normalizeError(error);
    res.status(apiError.statusCode).json({
      ok: false,
      error: apiError.toJSON(),
      timestamp: new Date().toISOString(),
    });
  }
}

/**
 * Optional authentication - doesn't fail if no token provided
 */
export function optionalAuth(req: Request, res: Response, next: NextFunction): void {
  const authHeader = req.headers.authorization;
  if (authHeader) {
    try {
      const [, token] = authHeader.split(' ');
      const payload = JWTAuth.verify(token);
      (req as any).user = payload;
    } catch (error) {
      // Silently fail - user will be undefined
    }
  }
  next();
}

// =====================================================================
// Permission Authorization
// =====================================================================

/**
 * Authorization middleware - checks if user has required permissions
 */
export function authorize(...requiredPermissions: Permission[]) {
  return (req: Request, res: Response, next: NextFunction): void {
    try {
      const user = (req as any).user as JWTPayload | undefined;

      if (!user) {
        throw new AuthenticationError('Authentication required');
      }

      // Admin has all permissions
      if (user.permissions.includes(Permission.ADMIN)) {
        return next();
      }

      // Check if user has all required permissions
      const hasPermissions = requiredPermissions.every((perm) =>
        user.permissions.includes(perm)
      );

      if (!hasPermissions) {
        throw new PermissionError('Insufficient permissions', {
          required: requiredPermissions,
          actual: user.permissions,
        });
      }

      next();
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
        timestamp: new Date().toISOString(),
      });
    }
  };
}

// =====================================================================
// Rate Limiting
// =====================================================================

interface RateLimitEntry {
  count: number;
  resetTime: number;
}

/**
 * In-memory rate limiter (use Redis in production)
 */
export class RateLimiter {
  private limits: Map<string, RateLimitEntry> = new Map();
  private readonly windowMs: number;
  private readonly maxRequests: number;

  constructor(windowMs: number = 60000, maxRequests: number = 100) {
    this.windowMs = windowMs;
    this.maxRequests = maxRequests;

    // Clean up expired entries every minute
    setInterval(() => this.cleanup(), 60000);
  }

  public check(key: string): RateLimitInfo {
    const now = Date.now();
    const entry = this.limits.get(key);

    if (!entry || now >= entry.resetTime) {
      // New window
      const resetTime = now + this.windowMs;
      this.limits.set(key, { count: 1, resetTime });
      return {
        limit: this.maxRequests,
        remaining: this.maxRequests - 1,
        reset: new Date(resetTime),
      };
    }

    // Within window
    entry.count++;

    if (entry.count > this.maxRequests) {
      throw new RateLimitError(Math.ceil((entry.resetTime - now) / 1000), {
        key,
        limit: this.maxRequests,
        resetTime: new Date(entry.resetTime),
      });
    }

    return {
      limit: this.maxRequests,
      remaining: this.maxRequests - entry.count,
      reset: new Date(entry.resetTime),
    };
  }

  private cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.limits.entries()) {
      if (now >= entry.resetTime) {
        this.limits.delete(key);
      }
    }
  }
}

// Global rate limiter instance
const globalRateLimiter = new RateLimiter();

/**
 * Rate limiting middleware
 */
export function rateLimit(windowMs?: number, maxRequests?: number) {
  const limiter = windowMs && maxRequests ? new RateLimiter(windowMs, maxRequests) : globalRateLimiter;

  return (req: Request, res: Response, next: NextFunction): void {
    try {
      // Generate key from IP or user ID
      const user = (req as any).user as JWTPayload | undefined;
      const key = user?.sub || req.ip || 'anonymous';

      const info = limiter.check(key);

      // Add rate limit headers
      res.setHeader('X-RateLimit-Limit', info.limit);
      res.setHeader('X-RateLimit-Remaining', info.remaining);
      res.setHeader('X-RateLimit-Reset', info.reset.toISOString());

      next();
    } catch (error) {
      const apiError = normalizeError(error);
      res.status(apiError.statusCode).json({
        ok: false,
        error: apiError.toJSON(),
        timestamp: new Date().toISOString(),
      });
    }
  };
}

// =====================================================================
// Input Validation & Sanitization
// =====================================================================

/**
 * Path traversal prevention
 */
export function sanitizePath(path: string): string {
  // Remove null bytes
  path = path.replace(/\0/g, '');

  // Normalize path separators
  path = path.replace(/\\/g, '/');

  // Remove parent directory references
  const parts = path.split('/').filter((part) => part !== '..' && part !== '.');

  return parts.join('/');
}

/**
 * Command injection prevention
 */
export function validateCommand(command: string): void {
  // Only allow alphanumeric, whitespace, dashes, underscores, dots, and slashes
  if (!/^[a-zA-Z0-9\s\-_./:]+$/.test(command)) {
    throw new ValidationError('Command contains disallowed characters', {
      command,
      allowed: 'a-zA-Z0-9 -_./:'
    });
  }

  // Prevent shell metacharacters
  const dangerous = ['|', '&', ';', '`', '$', '(', ')', '<', '>', '\n', '\r'];
  for (const char of dangerous) {
    if (command.includes(char)) {
      throw new ValidationError(`Command contains dangerous character: ${char}`, {
        command,
        dangerous: char,
      });
    }
  }
}

/**
 * SQL injection prevention (for any database operations)
 */
export function sanitizeSQL(input: string): string {
  return input.replace(/['";\\]/g, '');
}

/**
 * Input length validation
 */
export function validateLength(
  value: string,
  fieldName: string,
  min: number = 0,
  max: number = 10000
): void {
  if (value.length < min) {
    throw new ValidationError(`${fieldName} must be at least ${min} characters`, {
      field: fieldName,
      actual: value.length,
      min,
    });
  }

  if (value.length > max) {
    throw new ValidationError(`${fieldName} must be at most ${max} characters`, {
      field: fieldName,
      actual: value.length,
      max,
    });
  }
}

/**
 * Request body size limit middleware
 */
export function bodySizeLimit(maxSize: number = 10 * 1024 * 1024) { // 10MB default
  return (req: Request, res: Response, next: NextFunction): void {
    const contentLength = parseInt(req.headers['content-length'] || '0', 10);

    if (contentLength > maxSize) {
      const error = new ValidationError('Request body too large', {
        size: contentLength,
        limit: maxSize,
      });
      return res.status(error.statusCode).json({
        ok: false,
        error: error.toJSON(),
        timestamp: new Date().toISOString(),
      });
    }

    next();
  };
}

// =====================================================================
// CORS Configuration
// =====================================================================

/**
 * CORS middleware with origin whitelisting
 */
export function corsWithWhitelist(allowedOrigins: string[] = ['http://localhost:8010', 'http://127.0.0.1:8010']) {
  return (req: Request, res: Response, next: NextFunction): void {
    const origin = req.headers.origin;

    if (origin && allowedOrigins.includes(origin)) {
      res.setHeader('Access-Control-Allow-Origin', origin);
      res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      res.setHeader('Access-Control-Max-Age', '86400'); // 24 hours
    }

    // Handle preflight
    if (req.method === 'OPTIONS') {
      return res.status(204).end();
    }

    next();
  };
}
