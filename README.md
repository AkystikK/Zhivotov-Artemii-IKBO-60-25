Практические работы по конфигурационному управлению. Вариант 11.

- prac1.md — задания и решения по Bash.
- Emulator — первая практическая, этапы 1–3.
- DependencyGraph — вторая практическая, этапы 1–5.

Для программ нужен Python 3.10 или новее. Сторонние Python-библиотеки не нужны.
Команды ниже выполняются в PowerShell из корня репозитория.

Первая практическая

Эмулятор читает ZIP-архив в память. Содержимое файлов хранится в Base64.
Архив не изменяется, файлы на диск не извлекаются.
Команды ls и cd пока выводят имя и аргументы. Команда exit завершает программу.

Параметры:

- --vfs — обязательный путь к ZIP-архиву.
- --script — необязательный путь к текстовому файлу команд.

Создание тестовых архивов и запуск:

```powershell
$fixtures = Join-Path $env:USERPROFILE 'Documents\CodexScratch\tasks\2026-10-23-emulator-stage3\fixtures'
python -B Emulator/tests/create_vfs_fixtures.py --output-dir $fixtures
.\run.bat --vfs "$fixtures\deep.zip"
.\run.bat --vfs "$fixtures\deep.zip" --script Emulator/tests/startup_vfs.txt
```

В архиве deep.zip есть вложенные папки и двоичный файл.
При запуске выводится загруженная структура, затем можно вводить команды.
Пустая команда пропускается. Неизвестная команда выводит сообщение об ошибке.
При ошибке в стартовом файле его выполнение останавливается,
и программа переходит к вводу команд. Для выхода введи exit.
Относительные пути считаются от текущей папки терминала.

Функции в Emulator/src/main.py:

- run_command — обрабатывает команду.
- add_directory — добавляет папку в виртуальную файловую систему.
- load_vfs — загружает архив в словарь.
- print_vfs — выводит загруженную структуру.

Проверка после создания архивов:

```powershell
$env:VFS_FIXTURE_DIR = $fixtures
python -B -m unittest discover -s Emulator/tests -p 'test_*.py' -v
```

Вторая практическая

Программа читает настройки из CSV, получает сведения о Maven-пакетах,
строит граф зависимостей, определяет порядок загрузки и выводит PlantUML.

```powershell
.\DependencyGraph\run.bat
.\DependencyGraph\run.bat --order
.\DependencyGraph\run.bat --plantuml
```

Настройки, функции и проверки описаны в DependencyGraph/README.md.
