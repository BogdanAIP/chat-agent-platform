# Known Issues

1. Hosted Chat/MCP read/write/modify availability не проверена.
2. Branch/PR/Actions/merge path проверен; release пока не подписывается и не
   публикуется как versioned GitHub Release.
3. Python slice всё ещё присутствует как временный oracle; removal gate не пройден.
4. Artifact manifest защищён от concurrent writers и публикуется атомарно, но
   авария во время копирования может оставить незарегистрированный каталог;
   garbage collection/recovery strategy ещё не реализована.
5. Guarded prepare/confirm ещё не реализован.
6. Secret Store и consumer ACL представлены только schema/policy intent.
7. Async Job contract существует, runtime отсутствует.
8. Тестовый WAV синтетический; нужен пользовательский и benchmark corpus.
9. Git author identity берётся из авторизованного GitHub-профиля и настраивается
   только локально для этого репозитория.
10. Лицензия open-source проекта ещё не выбрана.
11. Rust runtime profile пока фиксирует compile-time minimum Rust version, а не
    полный вывод фактически установленного `rustc`.
