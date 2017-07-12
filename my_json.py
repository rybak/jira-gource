import json
import os

import myos

json_dir = 'json_dump'
myos.mkdir_p(json_dir)


def json_path(title: str) -> str:
    return json_dir + "/" + title + ".json"


def load_json(title: str):
    file = json_path(title)
    try:
        print("Loading json: ", file)
        print("Size of file: ", os.stat(file).st_size)
        with open(file, 'r') as jf:
            return json.load(jf)
    except FileNotFoundError:
        print("No file: " + file)
    except OSError:
        print("OSError while reading file: " + file)
    return None


def save_json(title: str, json_obj, pretty_print: bool = False):
    with open(json_path(title), 'w') as f:
        if pretty_print:
            json.dump(json_obj, f, indent=4)
        else:
            json.dump(json_obj, f)
