import { ValidationError } from './errors.js';

export interface DeviceEventRequest {
  deviceId: string;
  event: string;
}

export interface DeviceControlRequest {
  deviceId: string;
  action: string;
  params?: Record<string, any>;
}

export interface DeviceDiscoveryRequest {
  protocols?: string[];
  duration?: number;
}

export function handleDeviceEvent(req: DeviceEventRequest) {
  const deviceId = req.deviceId?.trim();
  const event = req.event?.trim();
  if (!deviceId || !event) {
    throw new ValidationError('Missing deviceId or event');
  }
  return { deviceId, event, timestamp: Date.now() };
}

export function controlDevice(req: DeviceControlRequest) {
  const { deviceId, action, params } = req;
  if (!deviceId || !action) {
    throw new ValidationError('Missing deviceId or action');
  }
  return {
    status: 'success',
    deviceId,
    action,
    params: params || {}
  };
}

export function discoverDevices(req: DeviceDiscoveryRequest) {
  const { protocols = ['mdns', 'ssdp', 'ble'], duration = 30 } = req;
  return {
    status: 'discovery_started',
    protocols,
    duration
  };
}

export function getDeviceStatus(deviceId: string) {
  if (!deviceId) {
    throw new ValidationError('Missing deviceId');
  }
  return {
    status: 'success',
    deviceId,
    online: true,
    lastSeen: Date.now()
  };
}
