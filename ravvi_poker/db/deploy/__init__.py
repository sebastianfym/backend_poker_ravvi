from pkg_resources import resource_listdir, resource_string


def getSQLFiles():
    result = []
    for name in resource_listdir(__package__, "."):
        if name[-4:] != ".sql" or name[3].lower() != "_":
            continue
        sql = resource_string(__package__, name).decode("utf8")
        result.append((name, sql))
    result.sort(key=lambda x: x[0])
    return result
