from importlib import resources

def getSQLFiles():
    result = []
    pkg = resources.files(__package__)
    for entry in pkg.iterdir():
        name = entry.name
        if name[-4:] != ".sql" or name[3].lower() != "_":
            continue
        sql = entry.read_text()
        result.append((name, sql))
    result.sort(key=lambda x: x[0])
    return result
