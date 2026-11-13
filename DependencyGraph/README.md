Вторая практическая работа. Вариант 11.

Программа анализирует зависимости Maven-пакетов. Выполнены этапы 1–5.
Нужен Python 3.10 или новее. Сторонние Python-библиотеки не используются.
Команды выполняются в PowerShell из корня репозитория.

Настройки

По умолчанию читается DependencyGraph/config.csv:

```csv
key,value
package,junit:junit
version,4.13.2
repository,https://repo.maven.apache.org/maven2
test_mode,false
```

- package — имя пакета в виде groupId:artifactId.
- version — версия пакета.
- repository — URL репозитория или путь к тестовому JSON-файлу.
- test_mode — false для Maven-репозитория, true для тестового файла.

Все четыре значения обязательны. Относительный путь к тестовому файлу
считается от папки CSV. Другой CSV выбирается параметром --config.

Запуск

```powershell
.\DependencyGraph\run.bat
.\DependencyGraph\run.bat --order
.\DependencyGraph\run.bat --plantuml
.\DependencyGraph\run.bat --config DependencyGraph/tests/config_shared.csv
```

- Без дополнительных параметров выводится граф.
- --order выводит порядок: зависимости раньше использующих их пакетов.
  При цикле такой порядок построить нельзя.
- --plantuml выводит описание диаграммы. Вместе с --order не используется.

Для проверки без интернета:

```powershell
.\DependencyGraph\run.bat --config DependencyGraph/tests/config_shared.csv --order
```

Результат:

```text
Loading order:
D -> B -> C -> A
```

Как работает

1. Читает и проверяет CSV.
2. Получает POM указанной версии и читает прямые зависимости.
3. Строит граф рекурсивным BFS. Уже найденные пакеты повторно не обрабатывает.
4. Вычисляет порядок загрузки.
5. Формирует текст PlantUML.

В тестовом режиме связи читаются из JSON. Имена пакетов — большие латинские буквы.

```json
{
    "A": ["B"],
    "B": []
}
```

Функции в src/main.py

- read_config — чтение CSV.
- validate_config — проверка настроек.
- resolve_value — подстановка свойств из POM.
- get_dependencies — получение прямых зависимостей и их версий.
- read_test_repository — чтение тестового JSON.
- bfs — обход графа по уровням с рекурсией.
- build_graph — выбор источника данных и построение графа.
- print_graph — вывод связей.
- loading_order — вычисление порядка загрузки.
- to_plantuml — преобразование графа в PlantUML.
- print_result — выбор вида вывода.
- main — запуск программы и обработка ошибок.

Проверка

```powershell
python -B -m unittest discover -s DependencyGraph/tests -p 'test_*.py' -v
.\DependencyGraph\tests\test_stage1.ps1
.\DependencyGraph\tests\test_stage2.ps1
.\DependencyGraph\tests\test_stage3.ps1
.\DependencyGraph\tests\test_stage4.ps1
.\DependencyGraph\tests\test_stage5.ps1
```

Автоматические Python-тесты работают без интернета.
Сценарии первого, второго и пятого этапов обращаются к Maven-репозиторию.
Сценарии третьего и четвёртого этапов используют локальные графы.

Примеры и сравнение

В examples лежат настройки, PlantUML и SVG для JUnit 4.13.2,
Hamcrest Library 1.3 и Hamcrest Core 1.3. SVG открываются в браузере.
Файлы с окончанием _maven получены отдельным запуском штатного инструмента Maven.

В JUnit-графе есть отличие: наша программа учитывает его тестовую зависимость
Hamcrest Library, а Maven не передаёт её использующему JUnit проекту.
В tests/MAVEN_COMPARISON.md записано сравнение порядка с Maven.

Ограничения

Читаются зависимости из самого POM. Наследование родительских POM и
dependencyManagement не реализованы. Подставляются свойства из текущего POM.
Обычный запуск не устанавливает библиотеки и не скачивает JAR.
Для превращения PlantUML в изображение нужен отдельный рендерер.
Код завершения: 0 при успехе, 1 при ошибке, 2 при неверных параметрах запуска.
