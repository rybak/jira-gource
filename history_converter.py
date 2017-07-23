import dateutil.parser as iso

from my_os import current_milli_time
import jira

HIST_CONV_DEBUG = False


def convert_history(modifications, create_modification, create_last_modification):
    print("Number of changes: ", len(modifications))
    print("Converting history...")
    start = current_milli_time()
    skipped = 0
    names = set()
    key = None
    try:
        for tk in sorted(modifications):
            h = modifications[tk]
            key = h['ticket']
            if 'author' not in h:
                skipped += 1
                # skipping automated transitions of tickets, e.g. by Bitbucket pull-requests and similar
                continue
            name = h['author']['displayName']
            names.add(name)
            email = h['author']['emailAddress']
            timestamp = h['created']
            iso_time = iso.parse(timestamp)
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
    print("Finished!")
    finish = current_milli_time()
    print("Converting took {0} ms.".format(finish - start))
    print("Number of skipped changes = ", skipped)
    print("Saving names of committers")
    # append, to avoid any data loss. Just `sort -u names.txt` later.
    with open("names.txt", "a") as f:
        f.write('\n' + "\n".join(names))
