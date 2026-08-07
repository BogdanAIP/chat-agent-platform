# Known Issues

1. Hosted Chat/MCP read/write/modify availability не проверена.
2. Branch/PR/Actions/merge path проверен; release пока не подписывается и не
   публикуется как versioned GitHub Release.
3. Python slice всё ещё присутствует как временный oracle; removal gate не пройден.
4. Неизвестный `art_*` каталог без валидного recovery record намеренно не
   удаляется автоматически: recovery помечает его unresolved, чтобы не потерять
   потенциально полезные данные. Отдельный operator cleanup пока отсутствует.
5. Guarded prepare/confirm ещё не реализован.
6. Async Job contract существует, runtime отсутствует.
7. Тестовый WAV синтетический; нужен пользовательский и benchmark corpus.
8. Git author identity берётся из авторизованного GitHub-профиля и настраивается
   только локально для этого репозитория.
9. Лицензия open-source проекта ещё не выбрана.
10. Rust runtime profile пока фиксирует compile-time minimum Rust version, а не
    полный вывод фактически установленного `rustc`.
