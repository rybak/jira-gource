import os
from subprocess import call, STDOUT

import history_converter
import jira


def create_commit(committer_name, committer_email, timestamp, commit_message):
    os.environ["GIT_COMMITTER_NAME"] = committer_name
    os.environ["GIT_AUTHOR_NAME"] = committer_name
    os.environ["GIT_COMMITTER_EMAIL"] = committer_email
    os.environ["GIT_AUTHOR_EMAIL"] = committer_email
    os.environ["GIT_AUTHOR_DATE"] = str(timestamp)
    os.environ["GIT_COMMITTER_DATE"] = str(timestamp)
    return call(['git', 'commit', '-m', commit_message])


def is_current_dir_git_repo():
    return call(['git', 'status'], stderr=STDOUT, stdout=open(os.devnull, 'w')) == 0


def create_repo(path: str):
    is_git_repo = is_current_dir_git_repo()
    if is_git_repo:
        print("Already a git repo")
        return False
    else:
        ret = call(['git', 'init'])
        if ret != 0:
            print("Something went wrong. Return code: {0}".format(ret))
            return False
        else:
            print("Created git repo in the directory {0}".format(path))
            return True


def create_modification(filename, author_name, author_email, timestamp):
    with open(filename, 'a') as f:
        f.write("Change by {n} @ {t}\n".format(n=author_name, t=timestamp))
    ret = call(['git', 'add', filename])
    if ret != 0:
        print("add failed")
        return False
    ret = create_commit(author_name, author_email, timestamp, "change {k}".format(k=filename))
    if ret != 0:
        print("commit failed")
        return False
    return True


def create_last_modification(filename, author_name, author_email, timestamp):
    ret = call(['git', 'rm', filename])
    if ret != 0:
        print("rm failed")
        return False
    ret = create_commit(author_name, author_email, timestamp, "last change {k}".format(k=filename))
    if ret != 0:
        print("commit failed")
        return False
    return True


def convert_history_to_git(modifications):
    history_converter.convert_history(modifications, create_modification, create_last_modification)


repo_path = os.path.join(os.path.expanduser("~"), 'temp_repo')
os.chdir(repo_path)
convert_history_to_git(jira.changes)
