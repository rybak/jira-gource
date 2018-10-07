from datetime import date
from configlib import *

my_user_name = "johnsmith"
jira_url = "https://jira.atlassian.com"

# Change this to a path to the certificate for your server or to False to
# completely ignore verification.  For more info see
# <http://docs.python-requests.org/en/master/user/advanced/#ssl-cert-verification>
verify = True


def skip_filter(changelog_entry) -> bool:
    """
    Predicate to tell whether or not specified changelog entry should be
    skipped.

    :param changelog_entry:
        The changelog entry of an issue to examine.
    :returns:
        A boolean, True to skip entry, False to keep it.
    """
    # this skip_filter skips any changelog entry which changes Workflow of
    # a ticket
    return is_field_change(changelog_entry, 'Workflow')


# Specify a way to extend the default sections of a ticket
JIRA_SERVER_COMPONENTS_KEY = 'components'


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
    components = get_compound_jira_field(issue_json, JIRA_SERVER_COMPONENTS_KEY,
                                         several_name="Multiple")
    if components:
        extra_sections.append(components)
    return extra_sections + sections


jira_server_project = {
    'min_key': 1,
    'max_key': 1000,
    'skip_dates': {
        date(1980, 1, 1),  # big ticket move
    },
    'skip_filter': skip_filter,
    'sections_extension': sections_extension_jira_server,
    'extra_fields': [JIRA_SERVER_COMPONENTS_KEY]
}

projects = {
    'JRASERVER': jira_server_project
}
