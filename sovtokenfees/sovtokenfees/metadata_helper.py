import json


def get_metadata(json_str, keys):
    md = json.loads(json_str)
    for key in keys:
        try:
            md[key]
        except KeyError:
            raise KeyError("{0} not found".format(key))
    return md
