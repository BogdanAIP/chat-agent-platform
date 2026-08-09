# Known Issues

Актуальные незакрытые ограничения. Закрытые исторические проблемы сюда не возвращать.

1. **Stage 4 final acceptance отложен.** Hosted Windows CI доказывает relay/gateway/auth/lifecycle, но реальный ChatGPT -> Yandex -> Windows -> ChatGPT `runtime_self_test` ещё не выполнен. До него remote surface ограничен `local_ping` и `runtime_self_test`.
2. **Stage 18 adapters не реализованы.** Guarded one-shot confirmation primitive уже есть, но ни один внешний publishing/distribution executor пока не имеет права выполнять side effect.
3. **Branch protection/ruleset не включён.** `main` технически допускает direct push; дисциплина branch -> PR -> CI -> squash merge пока процессная, а не принудительная настройка GitHub.
4. **Первый versioned release/tag ещё не выпускался.** Release workflow проверяет tag/main/version alignment, locked build, SBOM и SHA256SUMS; первый `v0.2.0` остаётся отдельной осознанной операцией.
5. **Release provenance ещё не включена.** После перевода repository в public GitHub artifact attestation стала доступна без прежнего private-repository ограничения; её нужно добавить в release workflow и проверить первым реальным tag.
6. **Python behavioral oracle всё ещё присутствует.** Он полезен для parity, но удваивает часть maintenance surface. Removal gate не пройден.
7. **Reference mastering benchmark технический, не музыкальный corpus.** Реальный Matchering engine и tonal/LUFS improvements проверяются на синтетическом PCM24 benchmark; subjective/professional quality на наборе реальных музыкальных материалов ещё не доказана.
8. **Artifact orphan cleanup намеренно консервативен.** Неизвестный `art_*` каталог без валидного recovery record сохраняется как unresolved, чтобы recovery не удалял потенциально полезные данные. Operator cleanup workflow пока отсутствует.
9. **Job/confirmation stores линейно сканируют JSON при отдельных lookup-сценариях.** Для текущего локального масштаба это приемлемо; retention/index нужны только после измеримого роста, а не как повод заранее вводить БД.
10. **Stage 16/17 остаются conditional.** Browser/video adapters не добавляются до конкретного пользовательского сценария и выбора лучшего бесплатного/opensource edge-инструмента.
11. **Способы добровольной поддержки проекта ещё не опубликованы.** MIT License уже действует независимо от донатов; адреса кошельков/другие способы поддержки нужно добавить позже, не превращая их в условие лицензии.
