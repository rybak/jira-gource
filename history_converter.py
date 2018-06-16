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
    if len(summary.strip()) == 0:
        return ""
    sections = list(filter(None, map(lambda s: s.strip().title(), summary.split(':'))))
    sections = sections[:-1]  # remove last bit of summary
    if config.sections_extension is not None:
        sections = config.sections_extension(jira.tickets_json[jira_key]['JIRA'], sections)
    if len(sections) == 0:
        return ""
    return '/'.join(sections) + '/'


def convert_history(modifications, create_modification, create_last_modification, generate_folders: bool = False):
    print("Number of changes: ", len(modifications))
    print("Converting history...")
    start = current_milli_time()
    skipped = 0
    names_file_path = 'names.txt'
    names = read_lines(names_file_path)
    key = None
    try:
        for tk in sorted(modifications):
            h = modifications[tk]
            key = h['ticket']
            if 'author' not in h:
                skipped += 1
                # skipping automated transitions of tickets, e.g. by Bitbucket pull-requests and similar
                continue
            name = h['author']['displayName']
            names.add(name)
            email = h['author']['emailAddress']
            timestamp = h['created']
            iso_time = iso.parse(timestamp)
            if HIST_CONV_DEBUG:
                print("{k}: @{t}: {n} <{e}>".format(k=key, t=iso_time, n=name, e=email))
            if generate_folders:
                filename = generate_folder(key) + key
            else:
                filename = key
            filename += generate_extension(key)
            if not create_modification(filename, name, email, iso_time):
                break

            # check if `h` is the last change on the `key` ticket
            last_change = jira.get_history(jira.tickets_json[key]['JIRA'])[-1]
            if last_change['created'] == timestamp:
                if not create_last_modification(filename, name, email, iso_time):
                    break
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
    print("Number of skipped changes = ", skipped)
    print("Saving names of committers in '{0}'".format(names_file_path))
    with open(names_file_path, 'w') as f:
        f.write("\n".join(sorted(names)))
    print("Saved!")
