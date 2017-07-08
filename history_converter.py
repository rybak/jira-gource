import os

import dateutil.parser as iso

import jira
import fake_git


repo_path = os.path.join(os.path.expanduser("~"), 'temp_repo')
os.chdir(repo_path)


def convert_history(sorted_modifications, create_modification, create_last_modification):
    names = set()
    try:
        for tk in sorted_modifications:
            h = sorted_modifications[tk]
            key = h['ticket']
            name = h['author']['displayName']
            names.add(name)
            email = h['author']['emailAddress']
            timestamp = h['created']
            iso_time = iso.parse(timestamp)
            print("{k}: @{t}: {n} <{e}>".format(k=key, t=iso_time, n=name, e=email))

            if not create_modification(key, name, email, iso_time):
                break

            # check if `h` is the last change on the `key` ticket
            last_change = jira.get_history(jira.tickets_json[key]['JIRA'])[-1]
            if last_change['created'] == timestamp:
                if not create_last_modification(key, name, email, iso_time):
                    break
    except KeyboardInterrupt:
        print("Interrupted by user. Stopping...")
    except Exception as e:
        print("Unexpected exception", e)
        print("Bailing out")
    print("Saving names of committers")
    # append, to avoid any data loss. Just `sort -u names.txt` later.
    with open("names.txt", "a") as f:
        f.write("\n".join(names))


def convert_history_to_git(sorted_modifications):
    convert_history(sorted_modifications, fake_git.create_modification, fake_git.create_last_modification)


convert_history_to_git(jira.sorted_changes)

