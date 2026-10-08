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
#!/bin/bash

file="$1"
firstLine=$(head -n 1 "$1")

case "$1" in
    *.c|*.js)
        pattern='^[[:space:]]*(//|/\*)'
        ;;

    *.py)
        pattern='^[[:space:]]*#'
        ;;

    *)
        echo 'Неподходящее расширение файла'
        exit 1
        ;;

esac

if [[ "$firstLine" =~ $pattern ]]; then
    echo "Комментарий есть"
else
    echo "Комментария нет"
fi
```

## Задание 7

```bash
#!/bin/bash

find "$1" -type f -exec sha256sum {} + | sort | uniq -w 64 -D
```

## Задание 8

```bash
#!/bin/bash

find "$1" -maxdepth 1 -type f -name "*.$2" -print0 | tar --null -cf archive.tar -T -
```

## Задание 9

```bash
#!/bin/bash

sed 's/    /\t/g' "$1" > "$2"
```

## Задание 10

```bash
#!/bin/bash

find "$1" -maxdepth 1 -type f -empty -printf '%f\n'
```
