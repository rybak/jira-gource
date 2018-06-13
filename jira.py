#!/usr/bin/env python3

import time
from getpass import getpass
import requests
import json
from datetime import datetime
import dateutil.parser as iso

from my_json import load_json, save_json
from my_os import read_lines

import config

JIRA_DEBUG = False
auth = None


def get_issue_url(issue_key: str) -> str:
    return config.jira_url + '/rest/api/2/issue/' + issue_key


def get_auth(my_login: str, prompt_line: str = "password:"):
    global auth
    if auth is None:
        print('url: {0}'.format(config.jira_url))
        print('login: {0}'.format(my_login))
        my_pass = getpass(prompt=prompt_line)
        auth = (my_login, my_pass)
    return auth


def reset_auth():
    global auth
    auth = None


def init_session() -> None:
    if auth is not None:
        return
    rest_session.auth = get_auth(my_login=config.my_user_name, prompt_line="jira pass:")
    rest_session.verify = config.verify


def download_issue(issue_key: str):
    if issue_key in missing_tickets:
        print("Skipping missing ticket {}".format(issue_key))
        return None
    result = None
    issue_url = get_issue_url(issue_key)
    print(datetime.now())
    print("Downloading: {}".format(issue_key))
    while True:
        try:
            init_session()
            r = rest_session.get(issue_url, params=params)
            if r.status_code != 200:
                print(r)
                print("Download failed for ticket {}".format(issue_key))
                if r.status_code == 401:
                    print("Wrong password")
                    reset_auth()
                    # go into while True again, ask for password one more time
                    continue
                if r.status_code == 403:
                    print("Need to enter CAPTCHA in the web JIRA interface")
                    reset_auth()
                    continue
                if r.status_code == 404:
                    print("No issue {}".format(issue_key))
                    missing_tickets.add(issue_key)
                break
            else:
                if JIRA_DEBUG:
                    print("url: {}".format(issue_url))
                print("Request successful: " + r.url)
                result = r.json()
                if JIRA_DEBUG:
                    print(str(json.dumps(r.json(), indent=4, separators=(',', ': '))))
                break  # whatever, still can return the json
        except requests.exceptions.ConnectionError as ce:
            clear_key(key)
            print("Connection error: {}".format(ce))
            print("You might need to define 'verify' in config.py.")
            print("Current value: config.verify =", config.verify)
            print("Waiting for {0} seconds...".format(NETWORK_ERROR_WAIT_DELAY))
            time.sleep(NETWORK_ERROR_WAIT_DELAY)
            # print("Trying again...")
            # might be useless to try again, return None
            break
    return result


def pretty_print(json_obj):
    print(str(json.dumps(json_obj, indent=4, separators=(',', ': '))))


def get_history(issue_json_obj):
    return issue_json_obj['changelog']['histories']


def get_key_str(key_num: int) -> str:
    return config.project + '-' + str(key_num)


def get_issue_json(k: str):
    if k not in tickets_json:
        return None
    return tickets_json[k]['JIRA']


NETWORK_ERROR_WAIT_DELAY = 5  # five seconds


def clear_key(k):
    if k in tickets_json:
        if 'downloaded' not in tickets_json[k]:
            tickets_json.pop(k, None)


def get_first_timestamp_or(issue_json_obj, default_value="Empty history") -> str:
    history_json = get_history(issue_json_obj)
    if len(history_json) == 0:
        return default_value
    return history_json[0]['created']


def filter_history(jira_key: str) -> None:
    issue = get_issue_json(jira_key)
    issue_history = get_history(issue)
    entries_to_remove = []
    for changelog_entry in issue_history:
        t = changelog_entry['created']
        iso_date = iso.parse(t).date()
        if JIRA_DEBUG:
            print(iso_date)
        if iso_date in config.skip_dates:
            entries_to_remove.append(changelog_entry)
        if config.skip_filter and config.skip_filter(changelog_entry):
            entries_to_remove.append(changelog_entry)
    for x in entries_to_remove:
        issue_history.remove(x)
    if len(entries_to_remove) > 0:
        print("Removed {0} changelog entries for ticket {1}".format(len(entries_to_remove), jira_key))


# Loading caches
# Note: user can manually add tickets to the missing-tickets.txt to skip them
missing_file_path = "missing-tickets.txt"
missing_tickets = read_lines(missing_file_path)
print("Missing tickets count = {}".format(len(missing_tickets)))
if JIRA_DEBUG:
    print("Missing tickets: ", ", ".join(sorted(missing_tickets)))

tickets_title = config.project + '-tickets'
tickets_json = load_json(tickets_title)
if tickets_json is None:
    tickets_json = {}

rest_session = requests.Session()

params = {
    'fields': 'key,summary',
    'expand': 'changelog'
}
if config.extra_fields is not None:
    params['fields'] = params['fields'] + ',' + config.extra_fields
# Download of tickets
for i in range(config.min_key, config.max_key):
    key = get_key_str(i)
    try:
        if key not in tickets_json:
            issue_json = download_issue(key)
            if issue_json is None:
                # could not download issue
                continue
            # store the ticket. Use 'JIRA' as key for the json part of the JIRA's response
            tickets_json[key] = {}
            tickets_json[key]['JIRA'] = issue_json
            # show the timestamp of the first item in the history to the user
            pretty_print(get_first_timestamp_or(issue_json))
            tickets_json[key]['downloaded'] = True
    except KeyboardInterrupt:
        clear_key(key)
        print("Interrupted by the user")
        break
    except Exception as e:
        clear_key(key)
        print("Unexpected exception: ", e)
        print("Key: ", key)
        print("Bailing out")
        break
    if key not in tickets_json:
        continue
    filter_history(key)

# store all the tickets
print("Total number of tickets: {0}".format(len(tickets_json)))
save_json(tickets_title, tickets_json)

print("Saving " + missing_file_path)
with open(missing_file_path, "w") as f:
    f.write("\n".join(sorted(missing_tickets)))
print("Saved!")

tickets_to_process = []
for i in range(config.min_key, config.max_key):
    key = get_key_str(i)
    if key not in tickets_json:
        continue
    issue_json = get_issue_json(key)
    if JIRA_DEBUG:
        print("Ticket : " + key)
        pretty_print(issue_json)
    tickets_to_process.append(key)

# Gather all change logs into one map
changes = {}
for key in tickets_to_process:
    issue_json = get_issue_json(key)
    history = get_history(issue_json)
    for h in history:
        timestamp = h['created']
        h['ticket'] = key
        changes[timestamp + key] = h
