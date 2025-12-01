import { ValidationError } from './errors.js';

export interface MeshTaskRequest {
  task: string;
  payload?: Record<string, any>;
  priority?: number;
}

export interface MeshNodeInfo {
  nodeId?: string;
  capabilities?: string[];
}

export function distributeTask(req: MeshTaskRequest) {
  const { task, payload = {}, priority = 0 } = req;
  if (!task) throw new ValidationError('Missing task');
  
  return {
    status: 'success',
    taskId: `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    task,
    priority,
    distributed: true
  };
}

export function getMeshStatus() {
  return {
    status: 'success',
    nodeCount: 1,
    role: 'leader',
    uptime: process.uptime()
  };
}

export function joinMesh(info: MeshNodeInfo) {
  const { nodeId, capabilities = [] } = info;
  return {
    status: 'success',
    message: 'Node joined mesh',
    nodeId: nodeId || `node_${Date.now()}`,
    capabilities
  };
}

export function getMeshNodes() {
  return {
    status: 'success',
    nodes: [],
    count: 0
  };
}
