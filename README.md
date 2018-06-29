JIRA → Gource converter
=======================

[JIRA][JIRA] is issue tracking software application, developed by Atlassian.

[Gource][Gource-homepage] is a version control visualization tool.

This script downloads history of issues from a JIRA server via [REST
API][JIRA-REST-API] and converts it into [custom format][Gource-custom-format],
allowing to visualize JIRA history using Gource.

![JIRA -> Gource screenshot](jira-gource.png)


Usage
-----

### Input

*See example of a configuration in file `config.sample.py`.*

The script's input is provided through a `config.py` file.  You need to provide:

* URL to the JIRA server
* JIRA login to use with REST API
* ID of the project
* Two integers `min_key` and `max_key`—bounds of the issue keys to download
* Optional `skip_filter`—a function which takes a changelog entry and returns
  a boolean—whether or not the changelog entry should be skipped in the
  output.  Use `None`, if you do not want to define a `skip_filter`.
* `skip_dates`—a set of dates, which you wish to skip in the output.
  Suggestions for dates to skip:

    * workflow transition—when all tickets have one field updated
    * big assignee transition—when a lot of tickets are reassigned

  These kinds of changes touch a lot of tickets and thus make for a bad
  visualization of JIRA history.  Use `set()` (empty set) if you do not want to
  skip any changelog entries.

* Optional `sections_extension`—a function to extend (or completely change)
  the default "fake folder" path for tickets.
* By default, script only downloads ticket's summary and changelog.  To make
  an interesting `sections_extension` function, you might need some other
  fields of the ticket.  This can be done by specifying these fields in config
  variable `extra_fields`.

Some helper functions are defined in `configlib.py` to make writing logic for
`config.py` easier.  All of these function operate on some JSON objects, like
issues and issues' changelog entries.  See [official Atlassian
documentation][JIRA-REST-API] for more details.

### Running

With `config.py` in place, launch jira-gource:

    $ python generate_gource.py

When the script starts downloading the tickets, it will prompt the user
for their JIRA password to authenticate with the JIRA server.

### Output

* `gource-input-<PROJECT>.txt`―JIRA history converted to the custom format
  used by Gource.  This file can be used by Gource directly, for example:

      $ gource gource-input-JRASERVER.txt

  For more details about using Gource, see [documentation][Gource-github]
  on github.

* `names.txt`—list of JIRA users who appeared in the history of downloaded
  tickets.  This list can be used to download the photos to use with Gource's
  `--user-image-dir` option.
* `json_dump/<ID>-tickets.json`—cache of downloaded tickets.  Delete
  this file if you want to re-download the tickets on the next launch.
* `missing-tickets.txt`―list of tickets, for which JIRA has returned
  [HTTP response code 404](https://en.wikipedia.org/wiki/HTTP_404), which
  would be skipped on the next launch of the script.

JIRA tickets do not have any inherent structure similar to a codebase in a
filesystem.  Script attempts to generate a pseudo folder structure from colon
separated prefixes in tickets summaries.  Issue type is used to create the file
extensions in the generated history.  Different file extensions result in
different colors of nodes in the Gource visualization.  For example: a "Task"
ticket PROJECT-42 with summary "System: Component: implement feature" will be
represented by `System/Component/PROJECT-42.Task` in the generated Gource input.

### Dependencies and compatibility

* [requests](http://python-requests.org) library—to talk to a JIRA server
  via REST API
* jira-gource uses Python 3 features and is not Python 2 compatible.
* jira-gource has only been tested with [JIRA version 7.1.6][JIRA-REST-API],
  but is probably compatible with all 7.* versions.


Contributing
------------

Feel free to open an issue or to submit a pull request in any of the
repositories.  Any feature-requests, suggestions, and questions are welcome.


Mirrors
-------

* https://github.com/rybak/jira-gource
* https://bitbucket.org/andreyrybak/jira-gource
* https://gitlab.com/andrybak/jira-gource


TODO
----

* Download avatars directly from JIRA server using URL of the following form
  `<JIRA-SERVER>/jira/secure/useravatar?size=large&ownerId=fred`
* Add ability to download several projects at once, and a way to combine
  several histories into one, perhaps grouping them in folders by project key
  (or a more detailed project name, see
  [GET project](https://docs.atlassian.com/software/jira/docs/api/REST/7.6.1/#api/2/project-getProject)),
  to complement the existing partition by summary prefixes (see function
  `generate_folder()` in `history_converter.py`) and custom folder (see
  description of `sections_extension` in "Input" section).
* Flip boolean logic from `skip_filter` to `changelog_predicate`, to correspond
  to the first parameter of Python's `filter` builtin.
* Retire `skip_dates`, as `skip_filter` is much more versatile.  In the sample
  `skip_dates` logic could be included into `skip_filter`.
* Refactor `config.extra_fields`.
* Rename `sections_extension` to something sensible.
* Clean up and document the code.
* Write release notes
* Release version 1.0

[Gource-homepage]: http://gource.io
[Gource-github]: https://github.com/acaudwell/Gource
[Gource-custom-format]: https://github.com/acaudwell/Gource/wiki/Custom-Log-Format
[JIRA]: https://www.atlassian.com/software/jira
[JIRA-REST-API]: https://docs.atlassian.com/software/jira/docs/api/REST/7.1.6
