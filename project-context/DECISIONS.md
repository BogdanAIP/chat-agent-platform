# Decisions

## ADR-001 — vertical slice before infrastructure

Начать с Stage 0–1 и реального `media.inspect`, не создавая transport, gateway,
workflow engine или отдельные services.

## ADR-002 — Python architecture spike + FFmpeg

Первый slice реализован на Python для дешёвой проверки binding, policy, contracts,
artifact manifest и FFmpeg. После v1.4 он классифицирован как временный behavioral
oracle, а не целевой platform core.

## ADR-003 — JSON-compatible YAML for bootstrap configs

Первые YAML-файлы записаны в JSON-синтаксисе (валидный YAML 1.2), чтобы не
добавлять parser dependency до появления реальной потребности в полном YAML.

## ADR-004 — JSON Schema as the contract validator

Стандартные execution contracts валидируются зрелой библиотекой `jsonschema`.
Собственная предметная логика остаётся в проекте, но реализация стандарта не
дублируется частичным самописным validator.

## ADR-005 — adopt v1.4 Rust-first / native-edge

Целевой локальный core поставляется как один Windows Rust binary. Выбор оправдан
process control, path/policy enforcement, низкой runtime-зависимостью и будущими
artifact/job/secret primitives. FFmpeg, REAPER, Blender, Browser и Git сохраняют
свои native interfaces; Rust-first не означает Rust-only.

## ADR-006 — strangler migration with behavioral parity

Python не переписывается одним risky change. Rust последовательно воспроизводит
тот же shared contract и fixtures; default переключается после parity; удаление
Python выполняется отдельным change set после стабилизационного gate.

## ADR-007 — autonomous implementation authority through Stage 19

Пользователь разрешил Chat самостоятельно вести реализацию до Stage 19
включительно и принимать технические решения без отдельного согласования, если
они служат целям проекта. Разрешение включает внедрение полезных технических
решений, но не отменяет architecture, quality, security, cost и no-zoo gates.

Это не разрешение на бесконечное расширение продукта: новый component/dependency
должен иметь измеримую пользу для Stage 0–19, не дублировать зрелый инструмент без
причины и оставаться заменяемым. Отдельная пользовательская authority всё ещё
нужна для необратимых/внешних действий, новых расходов, раскрытия секретов или
изменения продуктовой цели.
