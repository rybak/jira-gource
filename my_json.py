import json
import os

import my_os
from my_os import current_milli_time

json_dir = 'json_dump'
my_os.mkdir_p(json_dir)


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


def save_json(title: str, json_obj, pretty_print: bool = False, use_dumps: bool = True):
    start = current_milli_time()
    path = json_path(title)
    print("Saving '{0}'...".format(path))
    with open(path, 'w') as f:
        if pretty_print:
            json.dump(json_obj, f, indent=4)
        else:
            if use_dumps:
                # use dumps seems at least 5-6.5 times faster
                s = json.dumps(json_obj, separators=(',', ':'))
                f.write(s)
            else:
                json.dump(json_obj, f, separators=(',', ':'))
        finish = current_milli_time()
        print("Saving took {0} ms. {1}".format(int(finish - start), "using dumps" if use_dumps else "using dump"))
        print("Finished!")
