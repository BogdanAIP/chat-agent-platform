import * as z from 'zod/v4';

export const webOpenSchema = z.object({
  url: z.string().url().max(4096),
}).strict();

export const visualFallbackSchema = z.object({
  instruction: z.string().min(1).max(4096)
    .describe('Concrete visual instruction for one text-labeled control.'),
  targetText: z.string().min(1).max(2048)
    .describe('Visible text used for both exact accessibility preflight and reviewed visual grounding.'),
  semanticName: z.string().min(1).max(1024).optional()
    .describe('Compatibility alias only. If supplied, it must normalize exactly to targetText and cannot force a different semantic preflight.'),
}).strict();

export const interactionExpectedControlSchema = z.object({
  target: z.string().min(1).max(512).optional()
    .describe('Control ref whose fresh post-action state must be verified. Defaults to the action target when available.'),
  present: z.boolean().optional(),
  value: z.string().max(4096).optional(),
  checked: z.boolean().optional(),
  selected: z.boolean().optional(),
  enabled: z.boolean().optional(),
}).strict();

export const interactionExpectedSchema = z.object({
  url: z.string().url().max(4096).optional()
    .describe('Exact final HTTP/HTTPS URL expected after the interaction.'),
  control: interactionExpectedControlSchema.optional(),
}).strict();

export const webObserveSchema = z.object({
  operation: z.enum(['find', 'snapshot']),
  text: z.string().min(1).max(2048).optional(),
  regex: z.string().min(1).max(2048).optional(),
  target: z.string().min(1).max(4096).optional(),
}).strict();

export const webInteractSchema = z.object({
  operation: z.enum(['click', 'type']),
  target: z.string().min(1).max(4096).optional(),
  element: z.string().min(1).max(1024).optional(),
  doubleClick: z.boolean().optional(),
  text: z.string().max(200000).optional(),
  submit: z.boolean().optional(),
  slowly: z.boolean().optional(),
  visualFallback: visualFallbackSchema.optional(),
  expected: interactionExpectedSchema.optional(),
}).strict();

export const PUBLIC_BROWSER_CONTRACT = Object.freeze({
  web_open: Object.freeze({
    operations: Object.freeze(['navigate']),
    inputSchema: webOpenSchema,
  }),
  web_observe: Object.freeze({
    operations: Object.freeze(['find', 'snapshot']),
    inputSchema: webObserveSchema,
  }),
  web_interact: Object.freeze({
    operations: Object.freeze(['click', 'type']),
    inputSchema: webInteractSchema,
  }),
});
