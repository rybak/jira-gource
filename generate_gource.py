"""
Download JIRA history, convert it into Gource history, and save it in text file.
"""
import jira
from history_converter import convert_history
import config

from my_os import current_milli_time


def _create_gource(unix_time: int, filename: str, author_name: str,
                   is_last_change: bool):
    return "{}|{}|{}|{}".format(
        unix_time, author_name, ('D' if is_last_change else 'M'), filename)


def to_str(t) -> str:
    return _create_gource(*t)


changes, tickets_json = jira.download_projects(list(config.projects.keys()))
gource_list = []
for project_id in config.projects:
    project_changes = changes[project_id]
    project_gource_list = convert_history(tickets_json,
                                          project_id, project_changes,
                                          config.projects[project_id].get('sections_extension', None))
    gource_list.extend(project_gource_list)
gource_list = sorted(gource_list)

gource_input_txt = 'gource-input.txt'
try:
    start = current_milli_time()
    with open(gource_input_txt, "w", encoding='utf-8') as gource_file:
        gource_file.write("\n".join(map(to_str, gource_list)))
    print("Gource input is saved in '{0}'".format(gource_input_txt))
    finish = current_milli_time()
    print("\tSaving took {} ms.".format(finish - start))
except OSError:
    print("OSError while writing to file: " + gource_input_txt)
except KeyboardInterrupt:
    print("Interrupted by user. Stopping...")
except Exception as e:
    print("Unexpected exception", e)
    print("Bailing out")
finally:
    jira.save_cache()
