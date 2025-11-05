import { ValidationError } from './errors.js';

export interface MeshTaskRequest {
  task: string;
}

export function distributeTask(req: MeshTaskRequest) {
  const task = req.task?.trim();
  if (!task) throw new ValidationError('Missing task');
  // Placeholder implementation until mesh integration is complete
  return { distributed: task };
}
