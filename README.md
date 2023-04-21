# Poker Backend

## Build & install package

### Development (editable) setup

```
pip3 install --user -e .[tests]
```

### Build & install package

Build:
```
python3 ./setup.py bdist_wheel
```

Install
```
pip3 install -f ./dist ravvi-poker-backend
```

## Uninstall
```
pip3 uninstall -y ravvi-poker-backend
```
