import os
from subprocess import call

import dateutil.parser as ISO

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
        iso_time = ISO.parse(timestamp)
        print("{k}: @{t}: {n} <{e}>".format(k=key, t=iso_time, n=name, e=email))
        with open(key, 'a') as f:
            f.write("Change by {n} @ {t}\n".format(n=name, t=iso_time))
        ret = call(['git', 'add', key])
        if ret != 0:
            print("add failed")
            break
        ret = fake_git.create_commit(name, email, iso_time, "change {k}".format(k=key))
        if ret != 0:
            print("commit failed")
            break

        # check if `h` is the last change on the `key` ticket
        last_change = jira.get_history(jira.tickets_json[key]['JIRA'])[-1]
        if last_change['created'] == timestamp:
            # if h is the last change - delete the ticket file and commit again
            # h == last_change
            ret = call(['git', 'rm', key])
            if ret != 0:
                print("rm failed")
                break
            ret = fake_git.create_commit(name, email, iso_time, "last change {k}".format(k=key))
            if ret != 0:
                print("commit failed")
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

