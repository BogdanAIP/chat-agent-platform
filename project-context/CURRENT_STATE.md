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

Stage 12 — partial. Rust-модуль REAPER adapter содержит typed session/track/marker
specs, принимает только зарегистрированные и FFprobe-valid audio artifacts и
генерирует ограниченный Lua/ReaScript driver для track creation, media import,
markers, render settings и project save. Driver не содержит `os.execute`,
`io.popen` или generic `Main_OnCommand`; строки экранируются. `reaper-probe` только
обнаруживает `reaper.exe` через `REAPER_EXE` или стандартные Windows paths.

Подготовлена policy-gated capability `audio.reaper_render` и CLI `reaper-render`.
Она проходит Project Binding → locked selection → PEP → Artifact Store, запускает
только новый изолированный REAPER instance, ждёт completion marker после сохранения
`.rpp`, ограничивает authoring 45 секундами и render 3 минутами, затем принимает
render только после стабильного FFprobe-valid WAV и проверки sample rate через
Stage 11. Сохранённый `.rpp` и WAV импортируются обратно в Artifact Store, а
request-scoped `runtime/reaper/<request_id>` очищается и при успехе, и при ошибке.
Windows CI проверяет lifecycle helper на реально запускаемом изолированном child
process, strict Clippy и полную регрессию; REAPER на CI намеренно не эмулируется.
Новых зависимостей, daemon или постоянно работающего процесса не добавлено.

Stage 12 не считается завершённым: GitHub-hosted runner не имеет доверенной
установленной REAPER-среды, а Hosted Chat → local execution ещё не доказан. Exit
gate теперь сводится к реальному запуску одной подготовленной команды
`reaper-render` на установленном REAPER и получению валидированных `.rpp` + WAV
artifacts. До этого Stage 13 не начинается.

Stage 9 остаётся conditional: отдельный supervisor/service не создаётся без
независимого lifecycle requirement. Stage 10 имеет рабочий Windows CI baseline.

Приватный remote `BogdanAIP/chat-agent-platform` используется как versioned source
of truth. Изменения проходят отдельные ветки, draft PR, Windows CI и squash merge в
`main`.
