"""
Converts JIRA history into Gource history.
"""
import traceback
from datetime import datetime
from functools import lru_cache
from typing import List, Tuple

from my_os import current_milli_time, read_lines
import jira

HIST_CONV_DEBUG = False


def generate_extension(tickets_json, jira_key: str) -> str:
    issuetype = jira.get_issue_json(tickets_json, jira_key)['fields'] \
            .get('issuetype', {}) \
            .get('name', "")
    if len(issuetype.strip()) == 0:
        return ""
    return "." + issuetype.replace(" ", "")


def generate_folder(tickets_json, project_id: str, jira_key: str, extension) -> str:
    summary = jira.get_issue_json(tickets_json, jira_key)['fields']['summary']
    sections = list(map(lambda s: s.strip().title(), summary.split(':')))
    sections = sections[:-1]  # remove last bit of summary
    sections = list(filter(lambda s: len(s) < 50, sections))
    if extension is not None:
        sections = extension(jira.get_issue_json(tickets_json, jira_key), sections)
    sections.insert(0, project_id)
    return '/'.join(sections) + '/'


def convert_history(tickets_json,
                    project_id: str,
                    modifications: List[Tuple[int, str, str, bool]],
                    sections_extension):
    print("Number of changes: ", len(modifications))
    print("Converting history...")
    gource_list = []
    start = current_milli_time()
    names_file_path = 'names.txt'
    names = read_lines(names_file_path)
    key = None

    @lru_cache(maxsize=50000)
    def get_filename(jira_key: str) -> str:
        folder_path = generate_folder(tickets_json, project_id, jira_key, sections_extension)
        return folder_path + jira_key + generate_extension(tickets_json, jira_key)

    try:
        for (timestamp, key, name, is_last_change) in sorted(modifications):
            # TODO add name conversion for clearing "inactive user" markers
            names.add(name)
            if HIST_CONV_DEBUG:
                print("{k}: @{t}: {n}".format(
                    k=key,
                    t=datetime.fromtimestamp(timestamp),
                    n=name))
            filename = get_filename(key)
            gource_list.append((timestamp, filename, name, is_last_change))
    except KeyboardInterrupt:
        print("Interrupted by user. Stopping...")
    except Exception as e:
        print("Unexpected exception", e)
        print(traceback.format_exc())
        print("NONE" if key is None else key)
        print("Bailing out")
    print("Finished!")
    finish = current_milli_time()
    print("\tConverting took {0} ms.".format(finish - start))
    print("Saving names of committers in '{0}'".format(names_file_path))
    with open(names_file_path, 'w') as f:
        f.write("\n".join(sorted(names)))
    print("Saved!")
    print(get_filename.cache_info())
    return gource_list
