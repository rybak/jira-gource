import os
import dateutil.parser as ISO
from subprocess import call, STDOUT
import jira


def create_commit(committer_name, committer_email, timestamp, commit_message):
    is_git_repo = is_current_dir_git_repo()
    if not is_git_repo:
        print("Trying to create commit")
        print("Not a git repo")
        print("Bailing out")
        return -42
    os.environ["GIT_COMMITTER"] = committer_name
    os.environ["GIT_AUTHOR"] = committer_name
    os.environ["GIT_COMMITTER_EMAIL"] = committer_email
    os.environ["GIT_AUTHOR_EMAIL"] = committer_email
    os.environ["GIT_AUTHOR_DATE"] = str(timestamp)
    os.environ["GIT_COMMIT_DATE"] = str(timestamp)
    return call(['git', 'commit', '-m', commit_message])


def is_current_dir_git_repo():
    return call(['git', 'status'], stderr=STDOUT, stdout=open(os.devnull, 'w')) == 0


def create_repo(path: str):
    os.chdir(path)
    is_git_repo = is_current_dir_git_repo()
    if is_git_repo:
        print("Already a git repo")
        return True
    else:
        ret = call(['git', 'init'])
        if ret != 0:
            print("Something went wrong. Return code: {0}".format(ret))
            return False
        else:
            print("Created git repo in the directory {0}".format(path))
            return True


repo_dir = 'temp_repo'

if not create_repo(repo_dir):
    print("Failed to create git repo")
    exit(1)

tickets_to_process = []
for i in range(18000, 18010):
    key = jira.project + "-" + str(i)
    if key not in jira.tickets_json:
        continue
    ticket_json = jira.tickets_json[key]['JIRA']
    print("Ticket : " + key)
    # jira.pretty_print(jira.get_history(ticket_json))
    tickets_to_process.append(key)

changes = {}
for key in tickets_to_process:
    ticket_json = jira.tickets_json[key]['JIRA']
    history = jira.get_history(ticket_json)
    for h in history:
        timestamp = h['created']
        h['ticket'] = key
        changes[timestamp + key] = h

for tk in sorted(changes):
    h = changes[tk]
    key = h['ticket']
    name = h['author']['displayName']
    email = h['author']['emailAddress']
    timestamp = h['created']
    iso_time = ISO.parse(timestamp)
    print("{k}: @{t}: {n} <{e}>".format(k=key, t=iso_time, n=name, e=email))
    with open(key, 'a') as f:
        f.write("Change by {n} @ {t}".format(n=name, t=iso_time))
    call(['git', 'add', key])
    ret = create_commit(name, email, iso_time, "change")
    if ret != 0:
        print("failed")
        break

