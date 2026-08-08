# Known Issues

1. **Stage 4 real account-level exit gate ещё не пройден.** Hosted Windows CI уже
   доказывает relay contracts, Credential Manager, detached worker lifecycle,
   duplicate-response cache, gateway auth и `runtime_self_test`, но нужен один
   реальный маршрут ChatGPT → Yandex Function → пользовательский Windows
   `agent-platform.exe` → ответ обратно в ChatGPT.
2. **`main` технически не защищён branch ruleset/required checks.** Проект следует
   branch → draft PR → CI → squash merge, но GitHub пока не запрещает случайный
   прямой push. Это требует настройки репозитория через GitHub Settings.
3. **Release supply chain ещё не завершён.** CI собирает release binary, но нет
   versioned GitHub Release, SBOM/attestation и выбранной схемы подписи поставки.
4. **Guarded prepare/confirm ещё не реализован как полный двухфазный протокол.**
   Текущий PEP умеет `guarded` decision и confirmation binding, но внешние
   distribution/paid side effects нельзя считать готовыми до отдельного
   prepare → user confirm → execute gate.
5. **Python v0.1 остаётся behavioral oracle.** Rust давно является основным core,
   но removal gate Python oracle ещё не пройден; удалять его стоит после
   стабилизации transport/config hardening, а не во время активной миграции.
6. **Unknown Artifact Store orphan не удаляется автоматически.** `art_*` каталог без
   валидного recovery record сохраняется как unresolved, чтобы fail-closed recovery
   не уничтожил потенциально полезные данные. Operator cleanup/retention policy
   остаётся задачей Stage 20.
7. **Reference/mastering benchmark всё ещё ограничен.** Есть реальные FFmpeg/REAPER
   проверки и clean-runner Matchering benchmark, но нужен более широкий corpus
   реальной пользовательской музыки для оценки субъективного качества, жанровых
   случаев и regressions, а не только технического QC.
8. **Runtime capability profile сообщает minimum Rust toolchain, а не гарантирует
   наличие `rustc` на машине поставки.** Это намеренно: release binary не должен
   требовать установленный Rust compiler. Опциональные REAPER/Matchering должны
   показываться по runtime probe, а не по compile-time предположению.
9. **Open-source лицензия не выбрана.** Несмотря на open-source направление проекта,
   репозиторий остаётся `UNLICENSED`, пока не будет принято отдельное решение о
   лицензии и правилах распространения зависимостей/edge-компонентов.
10. **Yandex free tier не является архитектурной гарантией нулевой стоимости.**
    Relay спроектирован малым и выключенным по умолчанию, но реальное потребление
    Cloud Functions/Object Storage после пользовательского Stage 4 acceptance нужно
    измерить и зафиксировать в Stage 20 operations audit.
