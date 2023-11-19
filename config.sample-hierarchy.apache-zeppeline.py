from datetime import date
from configlib import *

# user name can be empty or with any value when use token authentification for jira server (token works without login)
my_user_name = "anonymous"
jira_url = "https://issues.apache.org/jira"

# Change this to a path to the certificate for your server or to False to
# completely ignore verification.  For more info see
# <http://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification>
verify = True


def skip_filter(changelog_entry, issue_json) -> bool:
    """
    Predicate to tell whether or not specified changelog entry should be
    skipped.

    :param changelog_entry:
        The changelog entry of an issue to examine.
    :param issue_json
        JSON object of a ticket, as per GET "issue" request of JIRA's REST API.
    :returns:
        A boolean, True to skip entry, False to keep it.
    """
    fixVersion = get_compound_jira_field(issue_json, "fixVersions", several_name="Multiple")

    # skip issues with non concrete versions
    if fixVersion in [None, "Multiple"]:
        return True;
    
    # side effect - save all uniq fix version for building hierarchy later
    if fixVersion not in allFixVersions:
        allFixVersions.append(fixVersion)

    return False 

# Specify a way to extend the default sections of a ticket
JIRA_SERVER_COMPONENTS_KEY = 'components'
FIX_VERSIONS_KEY = 'fixVersions'

# internal global variables for building hierarchy via fix versions
allFixVersions = []
hierarchicalFixVersions = {}

def sections_extension_jira_server(issue_json, sections):
    """
    Generate custom list of folders for the file of the ticket in the Gource
    input.  Component, which the ticket is related to, is used as a folder.
    Folder named "Multiple" is used when there are more than one components.
    When component is not defined, no additional folders are used.

    :param issue_json:
        JSON object of a ticket, as per GET "issue" request of JIRA's REST API.
    :param sections:
        Default list of folders, generated from summary of the ticket.
    :return:
        Customized list of folders.
    """
    extra_sections = []
    fixVersion = get_compound_jira_field(issue_json, FIX_VERSIONS_KEY, several_name="Multiple")

    _build_hierarchy_fix_versions()
    if fixVersion:
        for version_part in hierarchicalFixVersions.get(fixVersion).split("/"):
            extra_sections.append(version_part)

    return extra_sections

def _build_hierarchy_fix_versions():
    """
    Build hierarchical path for fix versions into hierarchicalFixVersions dict
    previos version (and its path) should be used for next version
    deep 2 lvl 1.0, 1.1 will be like 1.0/1.1, but 1.1.1 (1.0/1.1/1.1.1) wont be parent for 1.2, just 1.0/1.1/1.2
    except hotfix version - they always child of its parent
    """
    already_filled = len(hierarchicalFixVersions.keys()) > 0
    if already_filled:
        return
    
    get_major_minor_part = lambda s: list(map(int, s.split('.')[:2]))
    previous_version = None
    for version in sorted(allFixVersions, key=get_major_minor_part):
        previous_path = hierarchicalFixVersions.get(previous_version)
        if previous_path:
            current_version_path = '{}/{}'.format(previous_path, version)
        else:
            current_version_path = version

        hierarchicalFixVersions.update({version: current_version_path})
        
        is_hotfix_version = len(version.split('.')) > 2 and version.split('.')[2] != '0'
        if is_hotfix_version is not True:
            previous_version = version

    print('hierarchy is builded')
    

jira_server_project = {
    'min_key': 1,
    'max_key': 6000,
    'skip_dates': {
        date(1980, 1, 1),  # big ticket move
    },
    'skip_filter': skip_filter,
    'sections_extension': sections_extension_jira_server,
    'extra_fields': [FIX_VERSIONS_KEY]
}

projects = {
    'ZEPPELIN': jira_server_project
}
