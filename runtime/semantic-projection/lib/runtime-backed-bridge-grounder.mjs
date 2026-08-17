export function createRuntimeBackedBridgeGrounder(runner) {
  if (!runner || typeof runner.ground !== 'function') {
    throw new Error('Runtime-backed bridge grounder requires an object with ground().');
  }

  return async request => {
    if (!request || typeof request !== 'object' || Array.isArray(request)) {
      throw new Error('Runtime-backed bridge grounder request must be an object.');
    }
    if (typeof request.instruction !== 'string' || !request.instruction.trim()) {
      throw new Error('Structured visual target requires instruction for runtime-backed grounding.');
    }
    if (typeof request.kind !== 'string' || !request.kind.trim()) {
      throw new Error('Structured visual target requires kind for runtime-backed grounding.');
    }

    return runner.ground({
      imageBytes: request.imageBytes,
      mimeType: request.mimeType,
      width: request.width,
      height: request.height,
      coordinateSpace: request.coordinateSpace,
      instruction: request.instruction,
      kind: request.kind,
      targetText: request.targetText ?? null
    });
  };
}
