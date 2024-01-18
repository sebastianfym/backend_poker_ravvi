# Poker Backend

### Development (editable) setup

инициализация версии на основе информации из git
```
./build_version.py
```

установка editable пакета
```
pip3 install --user -e .[tests]
```

### Run local doker

запуск необходимых контейнеров
```
./docker/up.sh
```

инициализация кода и базы (удаление и создание в начальном состоянии)
```
./docker/init.sh
```

запуск poker api
```
./docker/run_api.sh
```

остановка контейнеров
```
./docker/down.sh
```