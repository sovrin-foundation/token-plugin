import json


def get_metadata(json_str, keys):
    md = json.loads(json_str)
    for key in keys:
        try: md[key]
        except: raise KeyError("%s not found" %key)
    return md
