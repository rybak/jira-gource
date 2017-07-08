import os

import dateutil.parser as iso

import jira
import fake_git


repo_path = os.path.join(os.path.expanduser("~"), 'temp_repo')
os.chdir(repo_path)

names = set()
try:
    for tk in sorted(jira.changes):
        h = jira.changes[tk]
        key = h['ticket']
        name = h['author']['displayName']
        names.add(name)
        email = h['author']['emailAddress']
        timestamp = h['created']
        iso_time = iso.parse(timestamp)
        print("{k}: @{t}: {n} <{e}>".format(k=key, t=iso_time, n=name, e=email))

        if not fake_git.create_modification(key, name, email, iso_time):
            break

        # check if `h` is the last change on the `key` ticket
        last_change = jira.get_history(jira.tickets_json[key]['JIRA'])[-1]
        if last_change['created'] == timestamp:
            if not fake_git.create_last_modification(key, name, email, iso_time):
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

