# Stage 4: comparison with Maven

Checked on 2026-11-12 with Maven 3.9.16 from IntelliJ IDEA and Java 27.
The reference command uses Maven Dependency Plugin 3.8.1, goal `resolve`.
Maven is only a reference tool; our Python application does not call it.

## Our result

Package: `junit:junit`, version `4.13.2`, repository Maven Central.

```text
Loading order:
org.hamcrest:hamcrest-core:1.3 -> org.hamcrest:hamcrest-library:1.3 -> junit:junit:4.13.2
```

The order follows the graph's dependency links: Hamcrest Library needs
Hamcrest Core, and the selected JUnit POM declares both. All scopes declared
in that POM are included by our existing graph reader.

## Observed Maven result

The reference POM in `maven/pom.xml` declares JUnit 4.13.2 as a dependency of
a small comparison project. Maven successfully resolved:

```text
The following files have been resolved:
   junit:junit:jar:4.13.2:compile -- module junit [auto]
   org.hamcrest:hamcrest-core:jar:1.3:compile -- module hamcrest.core (auto)
```

The fresh-cache log also shows the target JAR requests in this sequence:

```text
Downloading from central: .../junit/junit/4.13.2/junit-4.13.2.jar
Downloaded from central: .../junit/junit/4.13.2/junit-4.13.2.jar
Downloading from central: .../org/hamcrest/hamcrest-core/1.3/hamcrest-core-1.3.jar
Downloaded from central: .../org/hamcrest/hamcrest-core/1.3/hamcrest-core-1.3.jar
```

Plugin dependencies are omitted from this excerpt. Maven finished with
`BUILD SUCCESS`. These are observations of this run, not a guarantee about
Maven's network scheduling in every environment.

## Why the results differ

1. Our order means dependencies before dependent packages. Maven's resolution
   listing and network request sequence are not a topological loading plan.
   Downloading the selected JUnit JAR first does not require executing it.
2. JUnit's POM marks Hamcrest Library as `test`. Maven does not propagate
   that test dependency to a project that uses JUnit. Our simple reader lists
   all declared direct dependencies, so its graph includes Hamcrest Library.
3. Independent graph branches can have more than one correct dependency-first
   order. Matching a manager's display order is not required for correctness
   of that graph property.

The assignment does not define whether loading order means a dependency-first
plan or physical downloads. This implementation explicitly uses the former
and compares it with the observed native resolution/download output above.

References:
- [Maven dependency mechanism](https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html)
- [Maven dependency:resolve](https://maven.apache.org/plugins/maven-dependency-plugin/resolve-mojo.html)

## Reproduce

From the repository root in PowerShell:

```powershell
$scratch = Join-Path $env:USERPROFILE 'Documents\CodexScratch\tasks'
$task = Join-Path $scratch '2026-11-12-dependencygraph-stage4'
$work = Join-Path $task 'maven'
$env:JAVA_HOME = Join-Path $env:USERPROFILE '.jdks\openjdk-27'
$maven = 'C:\Program Files\JetBrains\IntelliJ IDEA 2026.2.3\plugins\maven-plugin\lib\maven3\bin\mvn.cmd'
.\DependencyGraph\tests\compare_maven.ps1 -WorkDir $work -Maven $maven
```

Adjust Java/Maven paths for another computer. The comparison uses pinned
JUnit settings in `config_compare.csv`, not the editable default config.
The script copies the reference POM into the supplied work directory. Maven
cache, build files, resolution output, and the log stay outside the project.

Full local evidence from the checked run is under the task's `maven` folder:
`maven.log` and `maven-resolved.txt`. The repository contains this excerpt and
reproduction files, not downloaded JARs or generated build data.
