def parse_query(args):
    result = {}

    q = ""
    for key, val in args.items():
        if len(val) == 0:
            q += key
            continue
        if val == "True":
            val = True
        if val == "False":
            val = False
        result[key] = val

    if q is None:
        return result
    if "q" in q:
        result["quiet"] = True
    if "A" in q:
        result["force-ansi"] = True
    if "I" in q:
        result["inverted_colors"] = True
    if "T" in q:
        result["no-terminal"] = True
    if "F" in q:
        result["no-follow-line"] = True

    for key, val in args.items():
        if val == "True":
            val = True
        if val == "False":
            val = False
        result[key] = val

    return result
