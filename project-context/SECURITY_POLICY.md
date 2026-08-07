# Security Policy

- Default deny для неизвестных capabilities, consumers и destinations.
- Model risk hints не являются authority.
- Writes разрешены только внутри однозначно bound project roots.
- Delete, publish, merge, secret/system changes и external private staging — guarded.
- Secrets хранятся только в системном Secret Store и выдаются по consumer ACL.
- Arbitrary shell не является публичной capability.
- Artifacts имеют classification; private/sensitive не уходят наружу по умолчанию.
- Logs/results не содержат raw secrets, cookies, signed URLs или binary payloads.
- Guarded confirmation привязан к action, parameters, artifact hash, destination,
  cost, expiry и idempotency key; token single-use.

