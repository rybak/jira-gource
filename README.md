JIRA → Gource converter
=======================

[JIRA](https://www.atlassian.com/software/jira) is issue tracking product,
developed by Atlassian.

[Gource](http://gource.io/) is a software version control visualization tool.

This script downloads history of issues from a JIRA server via [REST
API](https://docs.atlassian.com/jira/REST/server/)
and converts it into [custom
format](https://github.com/acaudwell/Gource/wiki/Custom-Log-Format),
which can be used as an input to Gource to visualize it.

![JIRA -> Gource screenshot](jira-gource.png)

Usage
-----

### Input

The script's input is provided through a `config.py` file.  Example is
provided in `config.py.sample`.  You need to provide:

* URL to the JIRA server
* your JIRA login to use with REST API
* ID of the project
* `min_key` and `max_key` - the bounds for the issue keys to download
* `skip_dates` - a set of dates, which you wish to skip in the output.
   Dates to skip are:

    * workflow transition - when all tickets have one field updated
    * big assignee transition - when a lot of tickets are reassigned

   These kinds of changes touch a lot of tickets and thus make for a bad
   visualization of JIRA history.

### Running

After you filled in `config.py`:

    $ python generate_gource.py

When the script starts downloading the tickets, it will prompt the user
for their JIRA password to authenticate with the JIRA server.

### Output

* `gource-input-<PROJECT>.txt` ― JIRA history converted to the custom format
  used by Gource.  This file can be used by Gource directly, for example:

      $ gource gource-input-JRASERVER.txt

* `names.txt` — list of JIRA users who appeared in the history of downloaded
  tickets.  This list can be used to download the photos to use with Gource's
  `--user-image-dir` option.
* `json_dump/<PROJECT>-tickets.json` — cache of downloaded tickets.  Delete
  this file if you want to re-download the tickets on the next launch.
* `missing-tickets.txt` ― list of tickets, for which JIRA has returned
  [HTTP response code 404](https://en.wikipedia.org/wiki/HTTP_404), which
  would be skipped on the next launch of the script

JIRA tickets do not have any inherent similar structure.
Script attempts to generate a pseudo folder structure from prefixes
in tickets summaries.  For example: ticket PROJECT-42 with summary
"Component: Area: implement feature" will result in path in the
generated Gource input "Component/Area/PROJECT-42"


### Dependencies

* [requests](http://python-requests.org) library — to talk to a JIRA server
  via REST API


Contributing
------------

This is not good example of proper Python. I have written this script over
the course of five months in my free time.

Feel free to open an issue or submit a pull request.

TODO
----

* Download avatars directly from JIRA server using URL of the following form
  `<JIRA-SERVER>/jira/secure/useravatar?size=large&ownerId=fred`
