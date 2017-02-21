import getpass

auth = None


def get_auth(my_login, prompt_line="password:"):
    global auth
    if auth is None:
        my_pass = getpass.getpass(prompt=prompt_line)
        auth = (my_login, my_pass)
    return auth


def reset_auth():
    global auth
    auth = None
