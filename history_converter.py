import dateutil.parser as iso

import jira

HIST_CONV_DEBUG = False


def convert_history(modifications, create_modification, create_last_modification):
    names = set()
    try:
        for tk in sorted(modifications):
            h = modifications[tk]
            key = h['ticket']
            name = h['author']['displayName']
            names.add(name)
            email = h['author']['emailAddress']
            timestamp = h['created']
            iso_time = iso.parse(timestamp)
            iso_date = iso_time.date()
            if iso_date in jira.skip_dates:
                continue
            if HIST_CONV_DEBUG:
                print("{k}: @{t}: {n} <{e}>".format(k=key, t=iso_time, n=name, e=email))

            if not create_modification(key, name, email, iso_time):
                break

            # check if `h` is the last change on the `key` ticket
            last_change = jira.get_history(jira.tickets_json[key]['JIRA'])[-1]
            if last_change['created'] == timestamp:
                if not create_last_modification(key, name, email, iso_time):
                    break
    except KeyboardInterrupt:
        print("Interrupted by user. Stopping...")
    except Exception as e:
        print("Unexpected exception", e)
        print("NONE" if key is None else key)
        print("Bailing out")
    print("Saving names of committers")
    # append, to avoid any data loss. Just `sort -u names.txt` later.
    with open("names.txt", "a") as f:
        f.write("\n".join(names))
