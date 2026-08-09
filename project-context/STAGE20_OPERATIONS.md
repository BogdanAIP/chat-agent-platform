# Stage 20 — Operations audit

Статус: **partial**. Большая часть технических эксплуатационных рисков уже закрыта автоматизированно. После перехода repository в public снят лимит hosted Actions и закрыт юридический gap: проект использует стандартную MIT License. Остались эксплуатационные/manual gates ниже.

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
- actual build `rustc` и package MSRV показываются отдельно.

### External-side-effect authority

- guarded action binding стабильно включает фактическое действие/параметры;
- confirmation имеет TTL 30–900 s и one-shot atomic consume;
- repeated prepare идемпотентен и не может продлить окно подтверждения;
- changed artifact/destination/binding, expiry и replay блокируются;
- concurrent double-consume выдаёт ровно один `ConfirmationPermit`;
- publishing/distribution executors пока отсутствуют, поэтому primitive не создаёт side effect сам по себе.

### Media/runtime reliability

- typed FFmpeg operations не принимают arbitrary argument arrays от Chat;
- short probes имеют отдельный timeout;
- media operations получают duration-aware timeout с floor/ceiling;
- EBU R128 inspection использует quiet frame logging и сохраняет final Summary;
- REAPER и Matchering изолированы как typed edge adapters;
- Stage 12 реальный пользовательский REAPER acceptance пройден;
- Stage 19 запускает реальный pinned Matchering engine и технический benchmark.

### Remote transport

- Yandex relay off by default и не требует inbound Windows port;
- local agent token и remote bearer независимы;
- local token хранится в Windows Credential Manager;
- публичный health минимален;
- cloud хранит только task/result/heartbeat JSON, без media/business logic;
- immutable task/result rendezvous не полагается на Python instance concurrency;
- hosted Windows E2E доказывает configure/start/retry/self-test/stop/offline lifecycle.

### Supply chain

- Rust 1.97.1 зафиксирован в CI;
- hosted FFmpeg зафиксирован на Chocolatey 9.0.0;
- Matchering зафиксирован на 2.0.6 / Python 3.10 edge runtime;
- `cargo-deny` проверяет bans/sources;
- RustSec advisories блокируют dependency-changing PR/push runs;
- CycloneDX SBOM генерируется pinned `cargo-cyclonedx 0.5.9` с `SOURCE_DATE_EPOCH`;
- Dependabot сгруппирован по weekly non-major updates;
- CI path filters и caches уменьшают стоимость/время hosted CI без удаления продуктовых gates;
- repository public, поэтому hosted Actions снова доступны без прежнего private spending-limit blocker.

### Licensing

- корневой `LICENSE` содержит стандартную MIT License;
- Rust workspace metadata использует SPDX `MIT`;
- Python package metadata ссылается на тот же `LICENSE`;
- добровольная поддержка проекта явно отделена от лицензионных прав и не создаёт дополнительного условия.

## Release packaging

Release workflow уже находится в `main` и реализует:

```text
existing vX.Y.Z tag reachable from main
  -> Rust/Python version consistency gate
  -> locked Windows release build
  -> reproducible CycloneDX SBOM
  -> binary + SBOM ZIP
  -> SHA256SUMS + self-check
  -> immutable GitHub Release assets
```

Workflow не создаёт tag сам и не перезаписывает существующий release. Первый реальный `v0.2.0` tag/release является отдельной осознанной операцией.

После перехода repository в public GitHub artifact provenance/attestation стала доступна без прежнего Enterprise-only ограничения private repository. Её следует добавить в release workflow до первого публичного релиза.

## Остающиеся ручные gates

1. **Stage 4 real ChatGPT acceptance** — один реальный ChatGPT-originated `runtime_self_test` через Yandex и пользовательский Windows agent.
2. **GitHub branch protection/ruleset** — включить технический запрет обхода PR/required checks; сейчас discipline process-based.
3. **First release tag** — после provenance hardening осознанно создать `v0.2.0` и проверить реальные release assets/checksums/attestation на GitHub.
4. **Real music corpus** — если reference mastering будет заявляться как профессиональный музыкальный продукт, добавить набор реальных лицензированных/собственных материалов и human listening acceptance.
5. **Support addresses** — добавить реальные способы добровольной поддержки проекта, когда они появятся; это не влияет на MIT License.

## Conditional follow-up, не блокирующий Stage 20 автоматически

- индекс/retention для JSON JobStore/ConfirmationStore — только после измеримого роста;
- operator cleanup unresolved ArtifactStore orphans — когда появится реальная эксплуатационная потребность;
- supervisor/service — только если ручной relay lifecycle перестанет быть достаточным;
- удаление Python oracle — отдельный migration gate после стабилизации Rust behavior.

## Stage 20 exit rule

Stage 20 можно пометить `done`, когда автоматические checks остаются зелёными и выполнены ручные gates, относящиеся к выбранной модели поставки. Conditional будущие продукты (browser/video/distribution) сами по себе не блокируют operations audit текущего core.
