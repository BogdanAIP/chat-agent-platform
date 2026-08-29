import { randomBytes } from 'node:crypto';

export const WORKSPACE_ARTIFACT_PROCEDURE = 'verified_workspace_artifact_v1';
const TASK_ID_RE = /^[0-9a-f]{32}$/;

export function prepareProcedureCorrelation(request) {
  if (request?.procedure !== WORKSPACE_ARTIFACT_PROCEDURE) {
    return { correlationTaskId: null, assignedTaskId: null };
  }

  const resumeTaskId = typeof request?.resume_task_id === 'string'
    ? request.resume_task_id
    : null;
  if (resumeTaskId !== null) {
    if (!TASK_ID_RE.test(resumeTaskId)) {
      throw new Error('resume_task_id must be a 32-character lowercase hex task id');
    }
    return { correlationTaskId: resumeTaskId, assignedTaskId: null };
  }

  const assignedTaskId = randomBytes(16).toString('hex');
  return { correlationTaskId: assignedTaskId, assignedTaskId };
}

export function procedureFailure(reason, correlationTaskId = null) {
  const payload = {
    schema_version: 1,
    status: 'error',
    reason,
    action_count: 0,
    ...(correlationTaskId === null ? {} : { resume_task_id: correlationTaskId })
  };
  return {
    content: [{ type: 'text', text: JSON.stringify(payload) }],
    structuredContent: payload,
    isError: true
  };
}
