from importlib import resources


def getJSONFiles():
    result = []
    pkg = resources.files(__package__)
    for entry in pkg.iterdir():
        name = entry.name
        if name[-5:] != ".json":
            continue
        json = entry.read_text()
        result.append((name, json))
    result.sort(key=lambda x: x[0])
    return result