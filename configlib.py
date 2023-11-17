"""
This module offers helper functions to be used in ``config.py``.

Functions in this module operate on JSON objects, which are a whole response or
part of a response from one of JIRA REST API methods.

- `Official Atlassian documentation of JIRA REST API
  <https://docs.atlassian.com/software/jira/docs/api/REST/7.1.6>`_
"""


def get_jira_field(issue_json, field_key: str,
                   default_value: str = None) -> str:
    """Get a value from a simple predefined field of an issue.

    :param issue_json:
        The JSON object to examine, which represents one issue (ticket),
        returned by method `issue` of JIRA REST API.
    :param field_key:
        JSON key of the predefined field.
    :param default_value:
        String to return, when the field is absent or its value is not defined.
    """
    return _get_field(issue_json, field_key, default_value, 'name')


def get_custom_field(issue_json, field_key: str,
                     default_value: str = None) -> str:
    """Get a value from a simple custom field of an issue.

    :param issue_json:
        The JSON object to examine, which represents one issue (ticket),
        returned by method `issue` of JIRA REST API.
    :param field_key:
        JSON key of the custom field.
    :param default_value:
        String to return, when the field is absent or its value is not defined.
    """
    return _get_field(issue_json, field_key, default_value, 'value')


def get_compound_jira_field(issue_json, field_key: str,
                            default_value: str = None,
                            several_name: str = "Several") -> str:
    """Get a value from a compound predefined field of an issue.

    :param issue_json:
        The JSON object to examine, which represents one issue (ticket),
        returned by method `issue` of JIRA REST API.
    :param field_key:
        JSON key of the predefined field.
    :param default_value:
        String to return, when the field is absent or its value is not defined.
    :param several_name:
        String to return, when the field has more than one value.
    """
    return _get_compound_field(issue_json, field_key, default_value,
                               several_name, 'name')


def get_compound_custom_field(issue_json, field_key: str,
                              default_value: str = None,
                              several_name: str = "Several") -> str:
    """Get a value from a compound custom field of an issue.

    :param issue_json:
        The JSON object to examine, which represents one issue (ticket),
        returned by method `issue` of JIRA REST API.
    :param field_key:
        JSON key of the custom field.
    :param default_value:
        String to return, when the field is absent or its value is not defined.
    :param several_name:
        String to return, when the field has more than one value.
    """
    return _get_compound_field(issue_json, field_key, default_value,
                               several_name, 'value')

def get_raw_custom_field(issue_json, field_key: str,
                              default_value: str = None,
                              multiple_value: str = None) -> str:
    """Get a raw value from a custom plugin field of an issue.
    for example:
    "customfield_10000": [
					"com.atlassian.greenhopper.service..@6c5f4a91[id=9129,rapidViewId=1432,state=CLOSED,name= Name 1,startDate=2021-11-22T14:03:00.000+03:00,endDate=2021-12-06T14:03:00.000+03:00,completeDate=2021-12-07T11:08:56.178+03:00,activatedDate=2021-11-22T16:42:48.614+03:00,sequence=8164,goal=some description about a goal,autoStartStop=false]",
					"com.atlassian.greenhopper.service..@44220ba2[id=9206,rapidViewId=1432,state=CLOSED,name= name 2,startDate=2021-12-06T18:00:00.000+03:00,endDate=2021-12-20T18:00:00.000+03:00,completeDate=2021-12-21T13:16:54.613+03:00,activatedDate=2021-12-07T11:09:33.366+03:00,sequence=8343,goal=finish client functional,autoStartStop=false]"
				]

    :param issue_json:
        The JSON object to examine, which represents one issue (ticket),
        returned by method `issue` of JIRA REST API.
    :param field_key:
        JSON key of the custom field.
    :param default_value:
        String to return, when the field is absent or its value is not defined.
    :param multiple_value:
        String to return, when the field has more than one value, if None - then return first value.
    """
    return_first_value = multiple_value == None
    return _get_compound_field(issue_json, field_key, default_value, multiple_value, return_first_value = return_first_value)


def is_field_change(changelog_entry, field_key: str) -> bool:
    """Check if changelog entry contains field value change.

    :param changelog_entry:
        Changelog item to examime.
    :param field_key:
        Field to check.
    :return:
    """

    def is_field_change_item(changelog_item):
        return _is_field_change_item(changelog_item, field_key)

    if 'items' in changelog_entry:
        return any(map(is_field_change_item, changelog_entry['items']))
    return False


def _is_field_change_item(changelog_item, field_key: str) -> bool:
    return 'field' in changelog_item and changelog_item['field'] == field_key


def _get_field(issue_json, field_key: str, default_value: str = None,
               subscript: str = None) -> str:
    field = _extract_field(issue_json, field_key)
    if field is None:
        return default_value
    if subscript:
        return field[subscript]
    return field


def _get_compound_field(issue_json, field_key: str, default_value: str = None,
                        several_name: str = "Several",
                        subscript: str = None,
                        return_first_value: bool = False) -> str:
    field = _extract_field(issue_json, field_key)
    if field is None:
        return default_value
    if len(field) == 1 or (return_first_value and len(field) > 0):
        if subscript:
            return field[0][subscript]
        return field[0]
    else:
        return several_name


def _extract_field(issue_json, field_key: str):
    if 'fields' not in issue_json:
        return None
    fields = issue_json['fields']
    if field_key not in fields:
        return None
    field = fields[field_key]
    if not field:
        return None
    return field
