# Current State

Архитектура v1.4 — Rust-first/native-edge. Chat остаётся primary intelligence;
локальный `agent-platform.exe` применяет Project Binding, capability requirements,
locked tool selection, policy, Artifact Store и Secret Store, а зрелые программы
вызываются через ограниченные typed adapters. Python v0.1 сохранён только как
behavioral oracle для parity-проверок.

Hosted Chat → GitHub read/write подтверждён реальными branch/edit/PR/CI/merge
циклами через GitHub plugin. Hosted Chat → local execution transport и
account-level MCP write/modify ещё не проверены и не считаются доступными.
Подтверждённый локальный execution path — local/Codex CLI; отдельный transport,
daemon и supervisor не добавлены без доказанной lifecycle-потребности.

Stage 1 завершён: Rust vertical slice выполняет
`binding → policy → artifact → FFprobe/FFmpeg → validation → tool-v1` и совпадает
с Python oracle на реальном WAV. Stage 2 contracts встроены в binary; общие
positive/negative fixtures проходят Rust и Python. Stage 3 Project Memory,
Bootstrap и skills дают новой сессии минимальный связанный контекст вместо полного
дампа проекта.

Stage 6 завершён: `tools.yaml` + `tool-lock.yaml` выбирают executor после mandatory
quality/cost gates; PEP отделяет `decision` от `effective_risk`, model risk hint не
понижает enforcement, guarded confirmation привязан к capability/parameters/data
class/hash. `CapabilitySelection` неизменяем извне после выбора.

Stage 7 завершён: `SecretStore` использует Windows Credential Manager через safe
Rust backend без собственной криптографии, vault/daemon и `unsafe` в platform
crate. Metadata содержит только secret ref/ACL/credential target. Consumer identity
берётся из Stage 6 selection; raw secret существует только внутри короткого
callback и затем zeroize-ится. Windows integration test доказывает разрешённый
доступ и отказ `rust.local.ffmpeg` без утечки raw value.

Stage 8 завершён: Artifact Store использует pending lifecycle, per-artifact locks,
atomic publish/manifest update и recovery records. Manifest-loss recovery допускает
только contract/identity/path/SHA-256-valid artifact; неизвестные orphan directories
не удаляются. External staging разрешён только `public`/`project`, только
allowlisted executor identity, создаёт проверенную временную копию и всегда удаляет
её после callback. Recovery сбрасывает staging fail-closed.

Stage 11 завершён и подтверждён push-CI на `main`. Один FFmpeg adapter имеет typed
operations `media.inspect`, `media.validate`, `media.convert`,
`media.extract_audio`, `media.normalize_loudness` и `media.mux`. Convert принимает
только lossless WAV/FLAC; extract создаёт PCM 24-bit WAV; normalization использует
двухпроходный EBU R128 `loudnorm` с post-validation LUFS/true peak; mux копирует
video stream и добавляет FLAC audio в Matroska. Произвольные FFmpeg arguments,
output paths и shell наружу не выставлены.

Все Stage 11 операции проходят цепочку Project Binding → locked selection → PEP →
Artifact Store → FFmpeg timeout/kill → technical validation → `tool-v1`. FFmpeg
output сначала создаётся как временный файл, валидируется, импортируется в Artifact
Store и удаляется RAII cleanup. Реальные Windows integration tests проверяют
validate, FLAC conversion, PCM extraction, two-pass normalization, mux и rejection
неразрешённого AAC conversion.

Stage 12 завершён. Rust-модуль REAPER adapter содержит typed session/track/marker
specs, принимает только зарегистрированные и FFprobe-valid audio artifacts и
генерирует ограниченный Lua/ReaScript driver для track creation, media import,
markers, render settings и project save. Driver не содержит `os.execute`,
`io.popen` или generic `Main_OnCommand`; строки экранируются. `reaper-probe`
обнаруживает `reaper.exe` через `REAPER_EXE` или стандартные Windows paths.

Policy-gated capability `audio.reaper_render` проходит Project Binding → locked
selection → PEP → Artifact Store, запускает только новый изолированный REAPER
instance, ждёт completion marker после сохранения `.rpp`, ограничивает authoring 45
секундами и render 3 минутами, принимает render после стабильного FFprobe-valid WAV
и проверки sample rate через Stage 11. Сохранённый `.rpp` и WAV импортируются
обратно в Artifact Store, request-scoped workspace очищается при успехе и ошибке.

Реальный Stage 12 exit gate пройден 2026-08-08 на пользовательской Windows-машине с
установленным REAPER через `scripts/verify-reaper-stage12.ps1`: contract
`stage12-acceptance-v1` вернул `status=success`, создал и зарегистрировал `.rpp` и
48 kHz/2 s WAV, а SHA-256 обоих артефактов совпали с Artifact Store manifest.
Санитизированное evidence хранится в `project-context/STAGE12_ACCEPTANCE.md`.

Stage 13 завершён. Новый policy-gated `audio.mastering_analyze` использует уже
доказанный FFmpeg EBU R128 inspection и типизированный decision layer вместо
безусловного «сделать -14 LUFS». Профили `music-balanced`, `music-loud` и `speech`
задают target LUFS, true-peak ceiling и допустимый LRA envelope, а ответ сохраняет
исходные измерения, target, loudness delta, предлагаемое действие, quality flags,
причины, `auto_mastering_allowed` и `requires_review`.

Safe-auto gate требует review при неполных измерениях, sample rate ниже 44.1 kHz,
multichannel вне валидированного mono/stereo пути, LRA вне profile envelope и
вероятном clipping/нулевом true-peak headroom. Windows CI #95 прошёл реальные
PCM 24-bit WAV cases quiet/nominal/hot/32 kHz mono через полный
Project Binding → locked selection → PEP → Artifact Store → FFmpeg → decision путь,
плюс профильное сравнение одного источника, strict Clippy, contracts, Python
oracle/parity и release build. `project-context/STAGE13_BENCHMARK.md` фиксирует
границу: это профессиональный технический decision/QC layer, а не заявление, что
LUFS-анализ сам по себе заменяет художественный мастеринг.

Stage 14 завершён. `agent-platform.exe` теперь содержит собственный компактный
persistent job runtime вместо отдельного workflow-сервиса. `job-v1` хранится внутри
bound local root в `runtime/jobs/<project_id>`, записывается атомарно и защищён
межпроцессной блокировкой. Есть idempotent begin, status transitions, checkpoints,
cancellation, retryable failure, attempt counter и resume; checkpoint сохраняется
между retry. Persisted state повторно проходит contract/identity validation и
повреждение обрабатывается fail-closed без удаления evidence.

Windows CI #109 доказал конкурентную идемпотентность, запрет capability collision,
persistence через новые `JobStore`, retry/checkpoint semantics, terminal и
non-retryable denial и corrupt-state handling. Дополнительный integration test
запускает собранный `agent-platform` отдельными процессами для всего цикла begin →
resume → checkpoint → get → retryable fail → resume → succeed → get, поэтому
persistence подтверждена именно между process/session boundaries. Новый daemon,
workflow engine, database или runtime dependency не появился. Подробности в
`project-context/STAGE14_RUNTIME.md`.

Stage 15 завершён. Policy-gated `audio.mastering_produce` / `produce-master`
связывает Stage 13 decision layer, Stage 11 lossless/two-pass EBU R128 processing,
Artifact Store и Stage 14 persistent jobs. Idempotency key включает workflow
version, SHA-256 исходного файла, профиль и data class. Успешный повтор того же
запроса возвращает существующие job/master artifact/SHA-256 и не увеличивает
Artifact Store manifest.

Stage 13 остаётся authoritative safe-auto gate: review-required материал не может
стать успешным автоматическим master. Разрешены только `preserve` через lossless WAV
и `normalize_loudness`; arbitrary plug-in/FFmpeg/shell chain не выставляется.
Финальный WAV анализируется заново и должен пройти sample-rate ≥44.1 kHz,
mono/stereo, duration-drift ≤100 ms, Stage 13 safe-auto envelope, final action
`preserve` и true-peak ceiling. После этого master регистрируется в Artifact Store с
workflow/job/profile/QC provenance и persisted result.

Windows CI #119 прошёл реальные изолированные Project Binding сценарии: quiet
dynamic 48 kHz stereo → normalize → final preserve; exact repeat → тот же job,
artifact ID и SHA без нового manifest entry; already-compliant 48 kHz stereo →
preserve; 32 kHz mono → non-retryable `MASTERING_REVIEW_REQUIRED` и отсутствие
успешного master artifact. Строгие fmt/Clippy, все Rust tests, contracts, Python
oracle/parity и release build зелёные. `project-context/STAGE15_MASTERING.md`
фиксирует границу: это надёжный technical delivery master, а reference/тональный/
художественный mastering требует отдельной capability и отдельного benchmark.

После Stage 15 следующий доказанный функциональный gap — reference-based mastering,
который подходит под Stage 19 как отдельная профессиональная capability. Stage 16–18
остаются conditional и не реализуются автоматически без конкретного браузерного,
видео- или distribution-сценария. Отдельно остаётся ранний Stage 4 gap: Hosted Chat
→ local execution transport пока не доказан и должен быть закрыт тонким transport
решением либо явным ADR без разрастания media/business logic в transport.

Stage 9 остаётся conditional: отдельный supervisor/service не создаётся без
независимого lifecycle requirement. Stage 10 имеет рабочий Windows CI baseline.

Приватный remote `BogdanAIP/chat-agent-platform` используется как versioned source
of truth. Изменения проходят отдельные ветки, draft PR, Windows CI и squash merge в
`main`.
