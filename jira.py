#!/usr/bin/env python3

import time

import requests
import json
from datetime import date

from my_auth import *

project = "<PROJECT>"
my_user_name = "<USERNAME>"
jira_url = "<URL>"
DEBUG = False
min_key = 1
max_key = 100
skip_dates = {
    date(2006, 12, 18),
}


def get_issue_url(issue_key: str) -> str:
    return jira_url + '/rest/api/2/issue/' + issue_key


def json_path(title: str) -> str:
    return "json_dump/" + title + ".json"


def load_json(title: str):
    file = json_path(title)
    try:
        with open(file, 'r') as jf:
            return json.load(jf)
    except OSError:
        print("OSError while reading file: " + file)
    return None


def download_issue(issue_key: str):
    result = None
    issue_url = get_issue_url(issue_key)
    params = {
        "fields": "key,summary",
        "expand": "changelog"
    }
    while True:
        r = requests.get(issue_url,
                         params=params,
                         auth=get_auth(my_login=my_user_name, prompt_line="jira pass:"),
                         verify=False)
        if r.status_code != 200:
            print(r)
            print("Download failed for ticket ", issue_key)
            if r.status_code == 401:
                print("Wrong password")
                reset_auth()
                # go into while True again, ask for password one more time
                continue
            if r.status_code == 404:
                print("No issue ", issue_key)
            break
        else:
            print("url: ", issue_url)
            print("Request successful")
            result = r.json()
            if DEBUG:
                print(str(json.dumps(r.json(), indent=4, separators=(',', ': '))))
            break  # whatever, still can return the json
    return result


def pretty_print(json_obj):
    print(str(json.dumps(json_obj, indent=4, separators=(',', ': '))))


def get_history(issue_json_obj):
    return issue_json_obj['changelog']['histories']


tickets_title = project + '-tickets'
tickets_json = load_json(tickets_title)
if tickets_json is None:
    tickets_json = {}

print("Already saved: {0} tickets".format(len(tickets_json)))
NETWORK_ERROR_WAIT_DELAY = 5  # five seconds


def clear_key(k):
    if k in tickets_json:
        if 'downloaded' not in tickets_json[k]:
            tickets_json.pop(k, None)


def get_history_or(issue_json_obj, default_value="Empty history") -> str:
    history_json = get_history(issue_json_obj)
    if len(history_json) == 0:
        return default_value
    return history_json[0]['created']


for i in range(min_key, max_key):
    key = project + '-' + str(i)
    try:
        if key not in tickets_json:
            issue_json = download_issue(key)
            if issue_json is None:
                # could not download issue
                continue
            # store the ticket. Use 'JIRA' as key for the json part of the JIRA's response
            tickets_json[key] = {}
            tickets_json[key]['JIRA'] = issue_json
            # show the first item in the history to the user
            pretty_print(get_history_or(issue_json))
            tickets_json[key]['downloaded'] = True
    except KeyboardInterrupt:
        clear_key(key)
        print("Interrupted by the user")
        break
    except requests.exceptions.ConnectionError as ce:
        clear_key(key)
        print("Connection error: ", ce)
        print("Waiting for {0} seconds...".format(NETWORK_ERROR_WAIT_DELAY))
        time.sleep(NETWORK_ERROR_WAIT_DELAY)
        print("Trying again...")
    except Exception as e:
        print("Unexpected exception: ", e)
        print("Bailing out")
        break


def save_json(title: str, json_obj):
    with open(json_path(title), 'w') as f:
        json.dump(json_obj, f)


# store all the tickets
print("Total number of tickets: {0}".format(len(tickets_json)))
print("Saving " + json_path(tickets_title))
save_json(tickets_title, tickets_json)
print("Saved!")

tickets_to_process = []
for i in range(min_key, max_key):
    key = project + '-' + str(i)
    if key not in tickets_json:
        continue
    ticket_json = tickets_json[key]['JIRA']
    print("Ticket : " + key)
    # jira.pretty_print(jira.get_history(ticket_json))
    tickets_to_process.append(key)

changes = {}
for key in tickets_to_process:
    ticket_json = tickets_json[key]['JIRA']
    history = get_history(ticket_json)
    for h in history:
        timestamp = h['created']
        h['ticket'] = key
        changes[timestamp + key] = h

