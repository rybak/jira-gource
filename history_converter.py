import dateutil.parser as iso
import traceback

from my_os import current_milli_time, read_lines
import jira
import config

HIST_CONV_DEBUG = False


def generate_extension(jira_key: str) -> str:
    issuetype = jira.tickets_json[jira_key]['JIRA']['fields'] \
            .get('issuetype', {}) \
            .get('name', "")
    if len(issuetype.strip()) == 0:
        return ""
    return "." + issuetype.replace(" ", "")


def generate_folder(jira_key: str) -> str:
    summary = jira.tickets_json[jira_key]['JIRA']['fields']['summary']
    sections = list(map(lambda s: s.strip().title(), summary.split(':')))
    sections = sections[:-1]  # remove last bit of summary
    sections = list(filter(lambda s: len(s) < 50, sections))
    if config.sections_extension is not None:
        sections = config.sections_extension(jira.tickets_json[jira_key]['JIRA'], sections)
    # TODO (several projects) replace two lines with
    # TODO sections.insert(0, project_id)
    if len(sections) == 0:
        return ""
    return '/'.join(sections) + '/'


def convert_history(modifications, create_modification, create_last_modification):
    print("Number of changes: ", len(modifications))
    print("Converting history...")
    start = current_milli_time()
    names_file_path = 'names.txt'
    names = read_lines(names_file_path)
    key = None
    try:
        for (timestamp, key, name) in sorted(modifications):
            names.add(name)
            iso_time = iso.parse(timestamp)
            if HIST_CONV_DEBUG:
                print("{k}: @{t}: {n}".format(k=key, t=iso_time, n=name))
            filename = generate_folder(key) + key + generate_extension(key)
            create_modification(filename, name, iso_time)

            # TODO improve output by generating only one gource log line for
            # TODO the last change
            # check if it is the last change on the `key` ticket
            last_change = jira.get_history(jira.tickets_json[key]['JIRA'])[-1]
            if last_change['created'] == timestamp:
                create_last_modification(filename, name, iso_time)
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
