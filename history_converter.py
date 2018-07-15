import dateutil.parser as iso
import traceback
from functools import lru_cache

from my_os import current_milli_time, read_lines
import jira

HIST_CONV_DEBUG = False


def generate_extension(jira_key: str) -> str:
    issuetype = jira.get_issue_json(jira_key)['fields'] \
            .get('issuetype', {}) \
            .get('name', "")
    if len(issuetype.strip()) == 0:
        return ""
    return "." + issuetype.replace(" ", "")


def generate_folder(jira_key: str, extension) -> str:
    summary = jira.get_issue_json(jira_key)['fields']['summary']
    sections = list(map(lambda s: s.strip().title(), summary.split(':')))
    sections = sections[:-1]  # remove last bit of summary
    sections = list(filter(lambda s: len(s) < 50, sections))
    if extension is not None:
        sections = extension(jira.get_issue_json(jira_key), sections)
    # TODO (several projects) replace two lines with
    # TODO sections.insert(0, project_id)
    if len(sections) == 0:
        return ""
    return '/'.join(sections) + '/'


def _create_gource(filename, author_name, unix_time, gource_update_type):
    return "{t}|{u}|{c}|{f}".format(t=int(unix_time), u=author_name,
                                    f=filename, c=gource_update_type)


def _create_modification(filename, author_name, timestamp):
    unix_time = timestamp.timestamp()
    return _create_gource(filename, author_name, unix_time, 'M')


def _last_modification(filename, author_name, timestamp):
    unix_time = timestamp.timestamp()
    return _create_gource(filename, author_name, unix_time, 'D')


def convert_history(modifications, sections_extension):
    print("Number of changes: ", len(modifications))
    print("Converting history...")
    gource_list = []
    start = current_milli_time()
    names_file_path = 'names.txt'
    names = read_lines(names_file_path)
    key = None

    @lru_cache(maxsize=50000)
    def get_filename(jira_key: str) -> str:
        folder_path = generate_folder(jira_key, sections_extension)
        return folder_path + jira_key + generate_extension(jira_key)

    try:
        for (timestamp, key, name, is_last_change) in sorted(modifications):
            names.add(name)
            iso_time = iso.parse(timestamp)
            if HIST_CONV_DEBUG:
                print("{k}: @{t}: {n}".format(k=key, t=iso_time, n=name))
            filename = get_filename(key)
            if not is_last_change:
                gource_list.append(
                    _create_modification(filename, name, iso_time))
            else:
                gource_list.append(_last_modification(filename, name, iso_time))
    except KeyboardInterrupt:
        print("Interrupted by user. Stopping...")
    except Exception as e:
        print("Unexpected exception", e)
        print(traceback.format_exc())
        print("NONE" if key is None else key)
        print("Bailing out")
    print("Finished!")
    finish = current_milli_time()
    print("Converting took {0} ms.".format(finish - start))
    print("Saving names of committers in '{0}'".format(names_file_path))
    with open(names_file_path, 'w') as f:
        f.write("\n".join(sorted(names)))
    print("Saved!")
    print(get_filename.cache_info())
    return gource_list
