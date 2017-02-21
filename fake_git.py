import os


def create_commit(committer_name, committer_email):
    os.environ["GIT_COMMITTER"] = committer_name
    os.environ["GIT_AUTHOR"] = committer_name
    os.environ["GIT_COMMITTER_EMAIL"] = committer_email
    os.environ["GIT_AUTHOR_EMAIL"] = committer_email
    # TODO external git call
