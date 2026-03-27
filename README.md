# В чём суть?
![about.jpg](resources/about.jpg)

1 команда выполнялась Вадимом

2 команда Саматом

# 1 команда
Директория - `./first`

`securityApp.py` - основное приложение. Использует правила из `ruleManager.py`.

Перед запуском убедиться, что запущен контейнер с образом `onosproject/onos:latest` с параметрами по умолчанию.

Команда запуска: `docker run -d --name onos -p 8181:8181 -p 8101:8101 -p 5005:5005 -p 6653:6653 onosproject/onos:latest`

Также установите необходимые зависимости:
```bash
python3 -m venv .venv
source .venv/bin/activate # .venv/Scripts/activate для windows
pip install -r requirements.txt
```

После этого можно запускать `securityApp.py` из терминала

Для очистки информации по портам:
`sudo mn -c`

Предварительно `mininet` должен быть установлен. [См. оф доку](https://mininet.org/download/)

# 2 команда

# Результат
