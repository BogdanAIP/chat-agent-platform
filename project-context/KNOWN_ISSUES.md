# Known Issues

Актуальные незакрытые ограничения. Закрытые исторические проблемы сюда не возвращать.

1. **Stage 4 final acceptance отложен.** Hosted Windows CI доказывает relay/gateway/auth/lifecycle, но реальный ChatGPT -> Yandex -> Windows -> ChatGPT `runtime_self_test` ещё не выполнен. До него remote surface ограничен `local_ping` и `runtime_self_test`.
2. **Stage 18 adapters не реализованы.** Guarded one-shot confirmation primitive уже есть, но ни один внешний publishing/distribution executor пока не имеет права выполнять side effect.
3. **Branch protection/ruleset не включён.** `main` технически допускает direct push; дисциплина branch -> PR -> CI -> squash merge пока процессная, а не принудительная настройка GitHub.
4. **Open-source лицензия не выбрана.** `LicenseRef-UNLICENSED` — валидная SPDX custom reference для metadata/SBOM, но не лицензия и не разрешение на публичное распространение. Описание репозитория со словом `open-source` поэтому опережает юридическое состояние.
5. **Первый versioned release/tag ещё не выпускался.** Release workflow уже в `main` и технически проверяет tag/main/version alignment, locked build, SBOM и SHA256SUMS; первый `v0.2.0` остаётся отдельной осознанной операцией. Private repo на текущем доступе не имеет бесплатной GitHub artifact attestation.
6. **Python behavioral oracle всё ещё присутствует.** Он полезен для parity, но удваивает часть maintenance surface. Removal gate не пройден.
7. **Reference mastering benchmark технический, не музыкальный corpus.** Реальный Matchering engine и tonal/LUFS improvements проверяются на синтетическом PCM24 benchmark; subjective/professional quality на наборе реальных музыкальных материалов ещё не доказана.
8. **Artifact orphan cleanup намеренно консервативен.** Неизвестный `art_*` каталог без валидного recovery record сохраняется как unresolved, чтобы recovery не удалял потенциально полезные данные. Operator cleanup workflow пока отсутствует.
9. **Job/confirmation stores линейно сканируют JSON при отдельных lookup-сценариях.** Для текущего локального масштаба это приемлемо; retention/index нужны только после измеримого роста, а не как повод заранее вводить БД.
10. **GitHub Actions всё ещё расходуют private-repo minutes.** CI уже сужен по paths и использует caches/pinned tools. Пользователь отдельно разрешил сделать репозиторий public только если лимит Actions реально станет блокером; до этого приватность сохраняется.
11. **Stage 16/17 остаются conditional.** Browser/video adapters не добавляются до конкретного пользовательского сценария и выбора лучшего бесплатного/opensource edge-инструмента.
12. **Release provenance ограничена private-repo возможностями.** Checksums + SBOM доступны; GitHub artifact attestation следует добавить, если репозиторий станет public либо появится подходящий Enterprise entitlement.
