#!/usr/bin/env python3

import time
from getpass import getpass
import requests
import json
from datetime import datetime
import dateutil.parser as iso
from typing import List

from my_json import load_json, save_json
from my_os import read_lines

import config

JIRA_DEBUG = False
auth = None


def get_issue_url(issue_key: str) -> str:
    return config.jira_url + '/rest/api/2/issue/' + issue_key


def get_auth():
    global auth
    if auth is None:
        print('url: {0}'.format(config.jira_url))
        print('login: {0}'.format(config.my_user_name))
        my_pass = getpass(prompt="jira pass:")
        auth = (config.my_user_name, my_pass)
    return auth


def reset_auth():
    global auth
    auth = None


def init_session() -> None:
    if auth is not None:
        return
    rest_session.auth = get_auth()
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
            # session is initialized lazily to avoid asking for password if
            # all issues are already downloaded
            init_session()
            r = rest_session.get(issue_url, params=params)
            if JIRA_DEBUG:
                pretty_print(r.json())
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
                print("Request successful: " + r.url)
                result = r.json()
                break  # whatever, still can return the json
        except requests.exceptions.ConnectionError as ce:
            clear_key(key)
            print("Connection error: {}".format(ce))
            print("You might need to define 'verify' in config.py.")
            print("Current value: config.verify =", config.verify)
            time.sleep(5)
            break
    return result


def pretty_print(json_obj):
    print(str(json.dumps(json_obj, indent=4, separators=(',', ': '))))


def _get_orig_history(jira_key: str):
    return get_issue_json(jira_key)['changelog']['histories']


def get_history(jira_key: str):
    return tickets_json[jira_key]['filtered_history']


def _put_history(jira_key: str, filtered: List):
    tickets_json[jira_key]['filtered_history'] = filtered


def get_key_str(key_num: int) -> str:
    return config.project + '-' + str(key_num)


def get_issue_json(k: str):
    if k not in tickets_json:
        return None
    return tickets_json[k]['JIRA']


def clear_key(k):
    if k in tickets_json:
        if 'downloaded' not in tickets_json[k]:
            tickets_json.pop(k, None)


def filtered_history(jira_key: str, p) -> List:
    issue_history = _get_orig_history(jira_key)
    old_len = len(issue_history)
    filtered = list(filter(p, issue_history))
    new_len = len(filtered)
    if new_len < old_len:
        print("Removed {0} changelog entries for ticket {1}".format(
            old_len - new_len, jira_key))
    return filtered


def is_good_date(skip_dates, changelog_entry):
    t = changelog_entry['created']
    iso_date = iso.parse(t).date()
    return iso_date not in skip_dates


# config independent
# Loading caches
# Note: user can manually add tickets to the missing-tickets.txt to skip them
missing_file_path = "missing-tickets.txt"
missing_tickets = read_lines(missing_file_path)
print("Missing tickets count = {}".format(len(missing_tickets)))
if JIRA_DEBUG:
    print("Missing tickets: ", ", ".join(sorted(missing_tickets)))
rest_session = requests.Session()

params = {
    'fields': 'key,summary,issuetype',
    'expand': 'changelog'
}


if len(config.skip_dates) == 0:
    if config.skip_filter is None:
        def entry_predicate(changelog_entry):
            return True
    else:
        def entry_predicate(changelog_entry):
            return not config.skip_filter(changelog_entry)
else:
    if config.skip_filter is None:
        def entry_predicate(changelog_entry):
            return is_good_date(config.skip_dates, changelog_entry)
    else:
        def entry_predicate(changelog_entry):
            return is_good_date(config.skip_dates, changelog_entry) and \
                   (not config.skip_filter(changelog_entry))

# config dependent
tickets_title = config.project + '-tickets'
tickets_json = load_json(tickets_title)
if tickets_json is None:
    tickets_json = {}

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
    _put_history(key, filtered_history(key, entry_predicate))

# store all the tickets
print("Total number of tickets: {0}".format(len(tickets_json)))
save_json(tickets_title, tickets_json)

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
project_changes = []
changes[config.project] = project_changes
for key in tickets_to_process:
    history = get_history(key)
    for h in history:
        if 'author' not in h:
            # skipping automated transitions of tickets, e.g. by Bitbucket
            # pull-requests and similar
            continue
        timestamp = h['created']
        name = h['author']['displayName']
        project_changes.append((timestamp, key, name))

print("Saving " + missing_file_path)
with open(missing_file_path, "w") as f:
    f.write("\n".join(sorted(missing_tickets)))
print("Saved!")
