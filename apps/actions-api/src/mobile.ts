import crypto from 'node:crypto';
import { executeAction } from './actions.js';
import { normalize } from './normalize.js';
import { ValidationError } from './errors.js';

interface TokenInfo {
  deviceId: string;
  expiresAt: number;
}

const TOKEN_TTL_MS = 60 * 60 * 1000;
const tokens = new Map<string, TokenInfo>();

export function createPairingToken(deviceId: string): string {
  if (!deviceId) {
    throw new ValidationError('deviceId is required');
  }
  const token = crypto.randomBytes(16).toString('hex');
  tokens.set(token, { deviceId, expiresAt: Date.now() + TOKEN_TTL_MS });
  return token;
}

export async function handleRemoteCommand(token: string, body: unknown): Promise<unknown> {
  const info = tokens.get(token);
  if (!info || info.expiresAt < Date.now()) {
    throw new ValidationError('Invalid token');
  }
  const norm = normalize(body as any);
  return await executeAction(norm);
}
