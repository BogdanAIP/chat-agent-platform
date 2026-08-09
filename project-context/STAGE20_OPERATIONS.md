# Stage 20 — Operations audit

Статус: **partial / manual-gated**. Автоматический technical/release hardening текущего core завершён. Репозиторий дополнительно защищён активным ruleset для `main`. Остались только два внешних acceptance gate: реальный ChatGPT-originated Stage 4 round trip и первый настоящий `v0.2.0` release.

## Автоматически доказано

### Execution integrity

- одна idempotent job имеет один физический executor благодаря per-job OS lock;
- crash/restart освобождает OS lock, persisted job/checkpoint остаётся для resume;
- workflow input сначала захватывается как immutable Artifact Store snapshot;
- SHA-256 policy/idempotency identity обязан совпасть с реально обработанным snapshot;
- corrupt persisted state fail-closed и сохраняется как evidence.

### Capability/config integrity

- unknown manifest/requirement fields отклоняются (`deny_unknown_fields`);
- locked executor обязан существовать и быть enabled;
- quality, reliability, determinism, execution path, fallback и cost проверяются кодом;
- runtime profile генерируется из того же locked selection set и regression-test сравнивает его с `tool-lock.yaml`;
- фактический build `rustc` и package MSRV показываются отдельно.

### External-side-effect authority

- guarded action binding стабильно включает фактическое действие/параметры;
- confirmation имеет TTL 30–900 s и one-shot atomic consume;
- repeated prepare идемпотентен и не может продлить окно подтверждения;
- changed artifact/destination/binding, expiry и replay блокируются;
- concurrent double-consume выдаёт ровно один `ConfirmationPermit`;
- publishing/distribution executors пока отсутствуют, поэтому primitive сам по себе не создаёт side effect.

### Media/runtime reliability

- typed FFmpeg operations не принимают arbitrary argument arrays от Chat;
- short probes имеют отдельный timeout;
- media operations получают duration-aware timeout с floor/ceiling;
- EBU R128 inspection подавляет покадровый шум и сохраняет final Summary;
- REAPER и Matchering изолированы как typed edge adapters;
- Stage 12 real-user REAPER acceptance пройден;
- Stage 19 запускает реальный pinned Matchering engine и технический benchmark.

### Remote transport

- Yandex relay off by default и не требует inbound Windows port;
- local agent token и remote bearer независимы;
- local token хранится в Windows Credential Manager;
- публичный health минимален;
- cloud хранит только task/result/heartbeat JSON, без media/business logic;
- immutable task/result rendezvous не полагается на Python instance concurrency;
- hosted Windows E2E доказывает configure/start/retry/self-test/stop/offline lifecycle;
- окончательный ChatGPT-originated round trip намеренно остаётся отдельным manual acceptance.

### Public CI / trusted workflow surface

- `ci / verify-windows` запускается на каждом PR и каждом push в `main`, без path bypass;
- Rust 1.97.1 и hosted FFmpeg 9.0.0 зафиксированы;
- все first-party GitHub Actions зафиксированы по immutable commit SHA;
- repository-wide test запрещает возврат mutable `actions/...@vN`;
- каждый `actions/checkout` явно использует `persist-credentials: false`;
- repository-wide test требует это для каждого checkout во всех workflow;
- Stage 4 и Stage 19 сохраняют отдельные scoped E2E gates;
- GitHub Actions spending-limit blocker исчез после перевода repository в public.

### Main branch governance

Активный repository ruleset `main-protection` применён к default branch и проверен через GitHub API:

- enforcement: `active`;
- bypass actors: none; current user cannot bypass;
- pull request обязателен, approvals `0`;
- required checks: `verify-windows`, `gitleaks-history`;
- strict up-to-date status-check policy включён;
- linear history обязателен;
- deletion и non-fast-forward/force-push заблокированы.

### Supply chain / secrets / licensing

- проект распространяется по стандартной MIT License без дополнительных обязательных условий;
- Rust Cargo metadata и Python PEP 639 metadata используют MIT;
- checksum-pinned cargo-deny 0.20.2 напрямую, без Action wrapper, проверяет licenses/bans/sources и RustSec advisories;
- dependency license allow-list явный, evidence-driven и без package-level license exceptions;
- checksum-pinned Gitleaks 8.30.1 сканирует полный reachable git history с `--redact=100`; первый public-history scan зелёный;
- CycloneDX SBOM генерируется pinned `cargo-cyclonedx 0.5.9` с `SOURCE_DATE_EPOCH`;
- checksum-pinned cargo-about 0.9.1 генерирует Windows third-party notices;
- `about.toml` обязан иметь тот же accepted SPDX set, что и `deny.toml`;
- реальный License Notices E2E успешно генерирует notice bundle для текущего Windows dependency graph;
- Dependabot сгруппирован по weekly non-major updates.

## Release path

Release workflow уже реализует и тестами фиксирует:

```text
existing exact vX.Y.Z tag reachable from main
  -> read versions from exact tag commit
  -> locked Windows release build
  -> reproducible CycloneDX SBOM
  -> MIT LICENSE + THIRD_PARTY_LICENSES.html
  -> exact-content Windows ZIP
  -> SHA256SUMS + self-check
  -> GitHub build-provenance attestation
  -> immutable GitHub Release
```

Дополнительный **Release Package E2E** без write/OIDC/attestation permissions уже реально прошёл:

- собирает настоящий Windows release binary;
- создаёт SBOM и license bundle отдельными jobs;
- переносит три набора файлов через GitHub Actions artifacts;
- скачивает их обратно в packaging job;
- вызывает тот же `scripts/assemble-release-package.sh`, который использует настоящий release workflow;
- проверяет точный состав ZIP и `SHA256SUMS`;
- успешно загружает dry-run package artifact.

Raw `agent-platform.exe` не публикуется как отдельный GitHub Release asset: нормальный binary distribution path — ZIP с `.exe`, SBOM, MIT LICENSE и third-party notices. Attestation выполняется **до** `gh release create`, поэтому её ошибка блокирует публикацию. Existing release assets не перезаписываются.

Первый реальный `v0.2.0` tag/release всё ещё является отдельной осознанной операцией: package mechanics уже доказаны, но tag-triggered GitHub Release/attestation нужно один раз принять на настоящем release.

## Остающиеся обязательные manual gates

1. **Stage 4 real ChatGPT acceptance** — один реальный ChatGPT-originated `runtime_self_test` через Yandex и пользовательский Windows agent.
2. **First release tag** — осознанно создать `v0.2.0` и проверить реальные GitHub Release assets, `SHA256SUMS` и provenance attestation.

## Conditional / non-blocking follow-up

- real licensed/owned music corpus + human listening acceptance — только перед subjective professional-quality claims;
- support/donation addresses — когда появятся, оставаясь добровольными и отдельно от MIT;
- operator cleanup unresolved ArtifactStore orphans — при реальной эксплуатационной потребности;
- Job/ConfirmationStore indexing/retention — только после измеримого роста;
- supervisor/service — только если явный relay lifecycle станет недостаточным;
- Python oracle removal — отдельный parity/stability migration gate;
- browser/video/distribution adapters — только после конкретного пользовательского сценария.

## Stage 20 exit rule

Stage 20 можно пометить `done`, когда автоматические gates остаются зелёными и выполнены два обязательных manual gates выше. Conditional будущие продукты и subjective-quality расширения сами по себе Stage 20 текущего core не блокируют.
