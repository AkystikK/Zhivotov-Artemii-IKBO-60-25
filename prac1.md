# Практическая работа №1
## Задание 1

``` bash
grep -o '^[^:]*' /etc/passwd | sort
```

## Задание 2

```bash
awk '$2 ~ /^[0-9]+$/ {print $2, $1}' /etc/protocols | sort -nr | head -n 5
```

## Задание 3

```bash
text="$1"

len=${#text}
border=""

for ((i=0; i<len+2; i++)); do
    border="$border-"
done

echo "+$border+"
echo "| $text |"
echo "+$border+"
```

## Задание 4

```bash
grep -o '[A-Za-z_][A-Za-z0-9_]*' "$1" | sort -u | paste -s -d ' '
```

## Задание 5

```bash
#!/bin/bash

chmod 755 "$1" &&
sudo cp "$1" /usr/local/bin/
```

## Задание 6

```bash

```

## Задание 7

```bash

```

## Задание 8

```bash

```

## Задание 9

```bash

```

## Задание 10

```bash

```
