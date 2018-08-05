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


def download_issue(issue_key: str, fields):
    result = None
    issue_url = get_issue_url(issue_key)
    print(datetime.now())
    print("Downloading: {}".format(issue_key))
    while True:
        try:
            # session is initialized lazily to avoid asking for password if
            # all issues are already downloaded
            init_session()
            r = rest_session.get(issue_url, params={'fields': fields, 'expand': 'changelog'})
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
            print("Connection error: {}".format(ce))
            print("You might need to define 'verify' in config.py.")
            print("Current value: config.verify =", config.verify)
            time.sleep(5)
            break
    return result


def pretty_print(json_obj):
    print(str(json.dumps(json_obj, indent=4, separators=(',', ': '))))


def _get_orig_history(tickets_json, jira_key: str):
    return get_issue_json(tickets_json, jira_key)['changelog']['histories']


def _pop_history(tickets_json, jira_key: str):
    return tickets_json[jira_key].pop('filtered_history')


def _put_history(tickets_json, jira_key: str, filtered: List):
    history = []
    last_index = len(filtered) - 1
    for i, h in enumerate(filtered):
        timestamp = int(iso.parse(h['created']).timestamp())
        name = h['author']['displayName']
        history.append((timestamp, jira_key, name, i == last_index))
    tickets_json[jira_key]['filtered_history'] = history


def get_key_str(project_id: str, key_num: int) -> str:
    return project_id + '-' + str(key_num)


def get_issue_json(tickets_json, k: str):
    if k not in tickets_json:
        return None
    return tickets_json[k]['JIRA']


def clear_key(tickets_json, k):
    if k in tickets_json:
        if 'downloaded' not in tickets_json[k]:
            tickets_json.pop(k, None)


def filtered_history(tickets_json, jira_key: str, p) -> List:
    issue_history = _get_orig_history(tickets_json, jira_key)
    old_len = len(issue_history)
    # automated transitions of issues, e.g. by Bitbucket, do not have author
    filtered = list(filter(lambda h: 'author' in h and p(h), issue_history))
    new_len = len(filtered)
    if new_len < old_len:
        print("Removed {0} changelog entries for ticket {1}".format(
            old_len - new_len, jira_key))
    return filtered


def is_good_date(bad_dates, changelog_entry):
    t = changelog_entry['created']
    iso_date = iso.parse(t).date()
    return iso_date not in bad_dates


# config independent
# Loading caches
# Note: user can manually add tickets to the missing-tickets.txt to skip them
missing_file_path = "missing-tickets.txt"
missing_tickets = read_lines(missing_file_path)
print("Missing tickets count = {}".format(len(missing_tickets)))
if JIRA_DEBUG:
    print("Missing tickets: ", ", ".join(sorted(missing_tickets)))
rest_session = requests.Session()

default_fields = 'key,summary,issuetype'
# Gather all change logs into one map
projects = {}


def download_project(project_id: str):
    if project_id in projects:
        return projects[project_id]

    skip_dates = config.skip_dates
    skip_filter = config.skip_filter
    if len(skip_dates) == 0:
        if skip_filter is None:
            def entry_predicate(changelog_entry):
                return True
        else:
            def entry_predicate(changelog_entry):
                return not skip_filter(changelog_entry)
    else:
        if skip_filter is None:
            def entry_predicate(changelog_entry):
                return is_good_date(skip_dates, changelog_entry)
        else:
            def entry_predicate(changelog_entry):
                return is_good_date(skip_dates, changelog_entry) and (not skip_filter(changelog_entry))

    # config dependent
    project_id = config.project
    min_key = config.min_key
    max_key = config.max_key
    extra_fields = config.extra_fields or ''
    tickets_title = project_id + '-tickets'
    tickets_json = load_json(tickets_title)
    if tickets_json is None:
        tickets_json = {}

    # Download of tickets
    for i in range(min_key, max_key):
        key = get_key_str(project_id, i)
        if key in missing_tickets:
            print("Skipping missing ticket {}".format(key))
            continue
        try:
            if key not in tickets_json:
                issue_json = download_issue(key, fields)
                if issue_json is None:
                    # could not download issue
                    clear_key(tickets_json, key)
                    continue
                # store the ticket. Use 'JIRA' as key for the json part of the JIRA's response
                tickets_json[key] = {}
                tickets_json[key]['JIRA'] = issue_json
                tickets_json[key]['downloaded'] = True
        except KeyboardInterrupt:
            clear_key(tickets_json, key)
            print("Interrupted by the user")
            break
        except Exception as e:
            clear_key(tickets_json, key)
            print("Unexpected exception: ", e)
            print("Key: ", key)
            print("Bailing out")
            break
        if key not in tickets_json:
            continue
        _put_history(tickets_json, key, filtered_history(tickets_json, key, entry_predicate))

    # store all the tickets
    print("Total number of tickets: {0}".format(len(tickets_json)))
    save_json(tickets_title, tickets_json)

    tickets_to_process = []
    for i in range(min_key, max_key):
        key = get_key_str(project_id, i)
        if key not in tickets_json:
            continue
        issue_json = get_issue_json(tickets_json, key)
        if JIRA_DEBUG:
            print("Ticket : " + key)
            pretty_print(issue_json)
        tickets_to_process.append(key)

    project_changes = []
    projects[project_id] = (project_changes, tickets_json)
    for key in tickets_to_process:
        history = _pop_history(tickets_json, key)
        project_changes.extend(history)

    print("Saving " + missing_file_path)
    with open(missing_file_path, "w") as f:
        f.write("\n".join(sorted(missing_tickets)))
    print("Saved!")
    return projects[project_id]
