/**
 * File Operations Service
 * Secure file system operations with path traversal prevention
 */

import {
  readFile,
  writeFile,
  copyFile,
  rename,
  unlink,
  mkdir,
  rmdir,
  readdir,
  stat,
  access,
} from 'fs/promises';
import { join, dirname, resolve, relative } from 'path';
import { constants } from 'fs';
import {
  FileReadRequest,
  FileWriteRequest,
  FileCopyRequest,
  FileMoveRequest,
  FileDeleteRequest,
  DirectoryListRequest,
  FileInfo,
} from '../types/index.js';
import {
  FileOperationError,
  ValidationError,
} from '../errors.js';
import { sanitizePath } from '../middleware/security.js';
import { logFileOperation } from '../middleware/audit.js';

/**
 * File operations service
 */
export class FileOperations {
  private static readonly MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

  /**
   * Read file contents
   */
  public static async readFile(
    request: FileReadRequest,
    userId?: string
  ): Promise<{ content: string }> {
    try {
      const safePath = this.validateAndSanitizePath(request.path);

      // Check file exists and is readable
      await access(safePath, constants.R_OK);

      // Check file size
      const stats = await stat(safePath);
      if (stats.size > this.MAX_FILE_SIZE) {
        throw new FileOperationError(
          'read',
          request.path,
          `File too large: ${stats.size} bytes (max: ${this.MAX_FILE_SIZE})`,
          { size: stats.size, limit: this.MAX_FILE_SIZE }
        );
      }

      // Read file
      const content = await readFile(safePath, {
        encoding: request.encoding || 'utf8',
        flag: request.flag || 'r',
      });

      logFileOperation('read', safePath, userId, true, {
        size: stats.size,
        encoding: request.encoding || 'utf8',
      });

      return { content: content.toString() };
    } catch (error) {
      logFileOperation('read', request.path, userId, false, {
        error: error instanceof Error ? error.message : String(error),
      });
      throw this.normalizeError('read', request.path, error);
    }
  }

  /**
   * Write file contents
   */
  public static async writeFile(
    request: FileWriteRequest,
    userId?: string
  ): Promise<{ ok: boolean; path: string }> {
    try {
      const safePath = this.validateAndSanitizePath(request.path);

      // Ensure directory exists
      await mkdir(dirname(safePath), { recursive: true });

      if (request.atomic) {
        // Atomic write: write to temp file, then rename
        const tempPath = `${safePath}.tmp.${Date.now()}`;
        await writeFile(tempPath, request.content, {
          encoding: request.encoding || 'utf8',
          mode: request.mode,
          flag: request.flag || 'w',
        });
        await rename(tempPath, safePath);
      } else {
        // Direct write
        await writeFile(safePath, request.content, {
          encoding: request.encoding || 'utf8',
          mode: request.mode,
          flag: request.flag || 'w',
        });
      }

      const stats = await stat(safePath);
      logFileOperation('write', safePath, userId, true, {
        size: stats.size,
        atomic: request.atomic || false,
      });

      return { ok: true, path: safePath };
    } catch (error) {
      logFileOperation('write', request.path, userId, false, {
        error: error instanceof Error ? error.message : String(error),
      });
      throw this.normalizeError('write', request.path, error);
    }
  }

  /**
   * Copy file or directory
   */
  public static async copyFile(
    request: FileCopyRequest,
    userId?: string
  ): Promise<{ ok: boolean; destination: string }> {
    try {
      const safeSource = this.validateAndSanitizePath(request.source);
      const safeDestination = this.validateAndSanitizePath(request.destination);

      // Check source exists
      await access(safeSource, constants.R_OK);

      // Check if destination exists
      if (!request.overwrite) {
        try {
          await access(safeDestination, constants.F_OK);
          throw new FileOperationError(
            'copy',
            request.destination,
            'Destination already exists',
            { overwrite: false }
          );
        } catch (error: any) {
          if (error.code !== 'ENOENT') throw error;
        }
      }

      // Ensure destination directory exists
      await mkdir(dirname(safeDestination), { recursive: true });

      // Copy file
      await copyFile(
        safeSource,
        safeDestination,
        request.overwrite ? 0 : constants.COPYFILE_EXCL
      );

      // Preserve timestamps if requested
      if (request.preserveTimestamps) {
        const stats = await stat(safeSource);
        // Note: Node.js doesn't have built-in utimes for copying, would need native module
      }

      logFileOperation('copy', `${safeSource} -> ${safeDestination}`, userId, true);

      return { ok: true, destination: safeDestination };
    } catch (error) {
      logFileOperation('copy', `${request.source} -> ${request.destination}`, userId, false, {
        error: error instanceof Error ? error.message : String(error),
      });
      throw this.normalizeError('copy', request.source, error);
    }
  }

  /**
   * Move/rename file
   */
  public static async moveFile(
    request: FileMoveRequest,
    userId?: string
  ): Promise<{ ok: boolean; destination: string }> {
    try {
      const safeSource = this.validateAndSanitizePath(request.source);
      const safeDestination = this.validateAndSanitizePath(request.destination);

      // Check source exists
      await access(safeSource, constants.R_OK);

      // Check if destination exists
      if (!request.overwrite) {
        try {
          await access(safeDestination, constants.F_OK);
          throw new FileOperationError(
            'move',
            request.destination,
            'Destination already exists',
            { overwrite: false }
          );
        } catch (error: any) {
          if (error.code !== 'ENOENT') throw error;
        }
      }

      // Ensure destination directory exists
      await mkdir(dirname(safeDestination), { recursive: true });

      // Move file
      await rename(safeSource, safeDestination);

      logFileOperation('move', `${safeSource} -> ${safeDestination}`, userId, true);

      return { ok: true, destination: safeDestination };
    } catch (error) {
      logFileOperation('move', `${request.source} -> ${request.destination}`, userId, false, {
        error: error instanceof Error ? error.message : String(error),
      });
      throw this.normalizeError('move', request.source, error);
    }
  }

  /**
   * Delete file or directory
   */
  public static async deleteFile(
    request: FileDeleteRequest,
    userId?: string
  ): Promise<{ ok: boolean; path: string }> {
    try {
      const safePath = this.validateAndSanitizePath(request.path);

      // Check file exists
      const stats = await stat(safePath);

      if (stats.isDirectory()) {
        if (request.recursive) {
          await rmdir(safePath, { recursive: true });
        } else {
          await rmdir(safePath);
        }
      } else {
        await unlink(safePath);
      }

      logFileOperation('delete', safePath, userId, true, {
        isDirectory: stats.isDirectory(),
        recursive: request.recursive || false,
      });

      return { ok: true, path: safePath };
    } catch (error) {
      logFileOperation('delete', request.path, userId, false, {
        error: error instanceof Error ? error.message : String(error),
      });
      throw this.normalizeError('delete', request.path, error);
    }
  }

  /**
   * List directory contents
   */
  public static async listDirectory(
    request: DirectoryListRequest,
    userId?: string
  ): Promise<{ files: FileInfo[] }> {
    try {
      const safePath = this.validateAndSanitizePath(request.path);

      // Check directory exists and is readable
      await access(safePath, constants.R_OK);
      const stats = await stat(safePath);

      if (!stats.isDirectory()) {
        throw new FileOperationError('list', request.path, 'Path is not a directory');
      }

      const files: FileInfo[] = [];

      if (request.recursive) {
        await this.listDirectoryRecursive(safePath, files, request.includeHidden || false);
      } else {
        const entries = await readdir(safePath);

        for (const entry of entries) {
          if (!request.includeHidden && entry.startsWith('.')) {
            continue;
          }

          const fullPath = join(safePath, entry);
          const stats = await stat(fullPath);

          files.push({
            path: fullPath,
            name: entry,
            size: stats.size,
            isDirectory: stats.isDirectory(),
            isFile: stats.isFile(),
            isSymlink: stats.isSymbolicLink(),
            createdAt: stats.birthtime,
            modifiedAt: stats.mtime,
            accessedAt: stats.atime,
            permissions: stats.mode.toString(8),
          });
        }
      }

      logFileOperation('list', safePath, userId, true, {
        count: files.length,
        recursive: request.recursive || false,
      });

      return { files };
    } catch (error) {
      logFileOperation('list', request.path, userId, false, {
        error: error instanceof Error ? error.message : String(error),
      });
      throw this.normalizeError('list', request.path, error);
    }
  }

  /**
   * Recursive directory listing
   */
  private static async listDirectoryRecursive(
    dir: string,
    files: FileInfo[],
    includeHidden: boolean
  ): Promise<void> {
    const entries = await readdir(dir);

    for (const entry of entries) {
      if (!includeHidden && entry.startsWith('.')) {
        continue;
      }

      const fullPath = join(dir, entry);
      const stats = await stat(fullPath);

      files.push({
        path: fullPath,
        name: entry,
        size: stats.size,
        isDirectory: stats.isDirectory(),
        isFile: stats.isFile(),
        isSymlink: stats.isSymbolicLink(),
        createdAt: stats.birthtime,
        modifiedAt: stats.mtime,
        accessedAt: stats.atime,
        permissions: stats.mode.toString(8),
      });

      if (stats.isDirectory()) {
        await this.listDirectoryRecursive(fullPath, files, includeHidden);
      }
    }
  }

  /**
   * Validate and sanitize file path
   */
  private static validateAndSanitizePath(path: string): string {
    if (!path || typeof path !== 'string') {
      throw new ValidationError('Invalid path provided', { path });
    }

    // Sanitize path
    const sanitized = sanitizePath(path);

    // Resolve to absolute path
    const absolute = resolve(sanitized);

    // Check for path traversal attempts
    if (absolute.includes('..')) {
      throw new ValidationError('Path traversal attempt detected', {
        original: path,
        sanitized,
        absolute,
      });
    }

    return absolute;
  }

  /**
   * Normalize file operation errors
   */
  private static normalizeError(operation: string, path: string, error: unknown): FileOperationError {
    if (error instanceof FileOperationError) {
      return error;
    }

    const err = error as any;
    const message = err.code === 'ENOENT'
      ? 'File or directory not found'
      : err.code === 'EACCES' || err.code === 'EPERM'
      ? 'Permission denied'
      : err.code === 'EEXIST'
      ? 'File or directory already exists'
      : err.message || 'Unknown error';

    return new FileOperationError(operation, path, message, {
      code: err.code,
      errno: err.errno,
    });
  }
}
