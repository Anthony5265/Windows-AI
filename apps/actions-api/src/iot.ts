import { ValidationError } from './errors';

export interface DeviceEventRequest {
  deviceId: string;
  event: string;
}

export function handleDeviceEvent(req: DeviceEventRequest) {
  const deviceId = req.deviceId?.trim();
  const event = req.event?.trim();
  if (!deviceId || !event) {
    throw new ValidationError('Missing deviceId or event');
  }
  // Placeholder implementation
  return { deviceId, event };
}

