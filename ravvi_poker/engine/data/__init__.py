from importlib import resources


def getJSONFiles():
    result = []
    pkg = resources.files(__package__)
    print(f'pkg: {pkg}')
    for entry in pkg.iterdir():
        name = entry.name
        if name[-5:] != ".json" or name[3].lower() != "_":
            continue
        json = entry.read_text()
        result.append((name, json))
    result.sort(key=lambda x: x[0])
    return result