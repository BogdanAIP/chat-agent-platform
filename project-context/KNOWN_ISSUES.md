# Known Issues

Актуальные незакрытые ограничения. Закрытые исторические проблемы сюда не возвращать.

1. **Stage 4 final acceptance ещё не выполнен.** Hosted Windows CI доказывает relay/gateway/auth/lifecycle, но реальный ChatGPT -> Yandex -> Windows -> ChatGPT `runtime_self_test` ещё не выполнен. До него remote surface ограничен `local_ping` и `runtime_self_test`.
2. **Branch ruleset не включён.** `main` технически всё ещё допускает обход PR-процесса. CI уже подготовлен для защиты: `verify-windows` и `gitleaks-history` существуют на каждом PR, но сам GitHub ruleset требует repository-admin настройки.
3. **Первый versioned release/tag ещё не выпускался.** Package E2E доказал Windows binary + SBOM + MIT LICENSE + third-party notices -> ZIP -> SHA256SUMS, а release workflow содержит provenance attestation и immutable publish, но реальный `v0.2.0` tag-triggered publish ещё не проверен.
4. **Stage 18 adapters не реализованы.** Guarded one-shot confirmation primitive есть, но ни один внешний publishing/distribution executor пока не имеет права выполнять side effect.
5. **Python behavioral oracle всё ещё присутствует.** Он полезен для parity, но удваивает часть maintenance surface. Removal gate не пройден.
6. **Reference mastering benchmark технический, не музыкальный corpus.** Реальный Matchering engine и tonal/LUFS improvements проверяются на синтетическом PCM24 benchmark; subjective/professional quality на наборе реальных музыкальных материалов ещё не доказана.
7. **Artifact orphan cleanup намеренно консервативен.** Неизвестный `art_*` каталог без валидного recovery record сохраняется как unresolved, чтобы recovery не удалял потенциально полезные данные. Operator cleanup workflow пока отсутствует.
8. **Job/Confirmation stores используют линейный JSON lookup в отдельных сценариях.** Для текущего локального масштаба это приемлемо; retention/index нужны только после измеримого роста, а не как повод заранее вводить БД.
9. **Способы добровольной поддержки проекта ещё не опубликованы.** MIT License действует независимо от донатов; адреса кошельков/другие способы поддержки нужно добавить позже, не превращая их в условие лицензии.
10. **Stages 16/17 и конкретные Stage 18 adapters остаются conditional.** Browser/video/distribution surface не добавляется до конкретного пользовательского сценария и выбора лучшего подходящего edge-инструмента.
