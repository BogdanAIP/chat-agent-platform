# Python-to-Rust Migration Plan

## Статус исходного кода

Python v0.1 — architecture spike и behavioral oracle. Он не является целевым
platform core v1.4, но остаётся исполняемым до достижения Rust parity.

## Что сохраняется без переписывания

- `config/*.yaml` как JSON-compatible YAML source of truth;
- `contracts/*.schema.json`;
- Project Memory и project skills;
- WAV fixtures и acceptance expectations;
- FFmpeg/ffprobe как native-edge executors;
- tool-v1 result shape и stable error semantics.

## Parity matrix

| Capability | Python oracle | Rust target | Removal gate |
|---|---|---|---|
| Project Binding | работает | done | unknown/duplicate project tests pass |
| Policy allow/deny | работает | done | false low-risk hint cannot bypass deny |
| Artifact import/hash | работает | done | containment, SHA-256 and manifest parity |
| FFprobe metadata | работает | done | duration/rate/channels/codec parity |
| FFmpeg EBU R128 | работает | done | LUFS/LRA parity on fixture |
| Tool request/result validation | работает | done | shared positive/negative fixtures pass |
| Runtime probe | работает | done | Rust/FFmpeg availability recorded |
| Bootstrap/audit | работает | done | Rust binary owns default path |

## Последовательность

1. Создать один Rust binary crate с модулями, не несколько services.
2. Реализовать `diagnose` и загрузку Project Binding.
3. Перенести policy evaluation.
4. Перенести artifact import/hash/manifest.
5. Перенести FFprobe/FFmpeg adapter и parsing.
6. Подключить shared JSON schemas/fixtures.
7. Запустить cross-language parity suite — done.
8. Переключить README default commands на Rust — done.
9. Оставить Python oracle на один стабилизационный этап — current.
10. Удалить Python package только отдельным change set после exit gate — pending.

## Запреты миграции

- не менять contract shape одновременно с портом;
- не добавлять MCP, transport, secrets или async jobs в Stage 1;
- не переходить на FFmpeg FFI;
- не дробить workspace на crates до реальной boundary;
- не объявлять parity по unit tests без реального WAV;
- не удалять fixtures вместе со старым runtime.
