# Current State

Локальная часть Stage 0–1 реализована как исполняемый vertical slice. Поддерживается
одна capability: `media.inspect` через FFmpeg/ffprobe. Сквозной тест создаёт
настоящий WAV, применяет policy до импорта, регистрирует artifact, измеряет
metadata/LUFS и валидирует ответ.

Hosted Chat transport и account-level MCP write/modify ещё не проверены и не
считаются доступными. Подтверждённый execution path сейчас — local/Codex CLI.

Stage 2 contracts формализованы JSON Schema и применяются в исполняемом пути.
Stage 3 начат: Bootstrap skill валиден, а команда `bootstrap` возвращает только
Project Binding, три минимальных context-файла и релевантный capability slice.
Generated `CHATGPT_CAPABILITIES.md` строится из requirements и runtime profile,
поэтому человекочитаемый audit не создаёт второй source of truth.

Архитектурный план v1.4 принят с Rust-first/native-edge. Python v0.1 заморожен как
architecture spike и behavioral oracle.

Rust Stage 1 завершён локально: один `agent-platform.exe` выполняет
`diagnose/probe/bootstrap/audit/self-test/inspect/inspect-artifact`, применяет
binding/policy, импортирует и хеширует artifact, вызывает FFmpeg/ffprobe и
валидирует contracts. Artifact Store блокирует параллельные записи, атомарно
публикует manifest, проверяет containment и SHA-256 при чтении по ID. Release
binary baseline — 5 808 640 bytes.
Rust/Python parity подтверждён на реальном WAV; typed inspection возвращает
integrated LUFS, LRA и true peak dBTP.

Stage 2 завершён: шесть schemas встроены в binary, общие positive/negative fixtures
проходят в Rust и Python. Stage 3 завершён: четыре skills валидированы и
forward-tested. Единый локальный `scripts/verify.ps1` проходит: 9 Rust-тестов и
8 Python oracle-тестов. Windows CI дважды прошёл на чистых GitHub-hosted runner'ах
для PR #1 и опубликовал release artifact. Внешние FFmpeg/ffprobe процессы
ограничены 60 секундами и принудительно
завершаются с retryable `TOOL_TIMEOUT` при зависании.

Приватный remote `BogdanAIP/chat-agent-platform` работает через авторизованный
GitHub CLI. Проверен полный цикл branch → draft PR → CI → ready → squash merge;
PR #1 слит в `main`.
