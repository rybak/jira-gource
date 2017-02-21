#!/usr/bin/env python3

import os
import sys

import requests
import json

from my_auth import *

project = "<PROJECT>"
my_user_name = "<USERNAME>"
jira_url = "<URL>"
DEBUG = False
min_key = 1
max_key = 100


def get_issue_url(issue_key):
    return jira_url + '/rest/api/2/issue/' + issue_key


def json_path(issue_key):
    return "json_dump/" + issue_key + ".json"


def load_json(filename):
    try:
        with open(filename, 'r') as json_file:
            return json.load(json_file)
    except OSError:
        print("OSError while reading file: " + filename)
    return None


def download_issue(issue_key):
    filename = json_path(issue_key)
    result = None
    if os.path.exists(filename):
        # already downloaded
        result = load_json(filename)
        return result
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
                continue
            if r.status_code == 404:
                print("No issue ", issue_key)
            break
        else:
            print("url: ", issue_url)
            print("Request successful")
            result = r.json()
            try:
                with open(filename, 'w') as issue_json_file:
                    json.dump(result, issue_json_file)
            except OSError as err:
                print("Error during dumping of ticket ", issue_key)
                print(err)
            except:
                print("Unexpected error:", sys.exc_info()[0])
                raise
            else:
                print("File written: ", issue_json_file)
            if DEBUG:
                print(str(json.dumps(r.json(), indent=4, separators=(',', ': '))))

            break  # whatever, still can return the json
    return result


def pretty_print(json_obj):
    print(str(json.dumps(json_obj, indent=4, separators=(',', ': '))))


def get_history(issue_json_obj):
    return issue_json_obj['changelog']['histories']


for i in range(min_key, max_key):
    key = project + "-" + str(i)
    issue_json = download_issue(key)
    if issue_json is None:
        continue
    pretty_print(get_history(issue_json)[0])


