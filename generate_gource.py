import jira
import history_converter
import config

DEBUG = False
gource_list = []


def write_gource(filename, author_name, unix_time, gource_update_type):
    gource_log_item = "{t}|{u}|{c}|{f}".format(t=int(unix_time), u=author_name, f=filename, c=gource_update_type)
    gource_list.append(gource_log_item)


def gource_modification(filename, author_name, author_email, timestamp) -> bool:
    unix_time = timestamp.timestamp()
    write_gource(filename, author_name, unix_time, 'M')
    return True


def gource_last_modification(filename, author_name, author_email, timestamp) -> bool:
    unix_time = timestamp.timestamp()
    write_gource(filename, author_name, unix_time, 'D')
    return True


history_converter.convert_history(jira.changes, gource_modification, gource_last_modification, generate_folders=True)

gource_input_txt = "gource-input-{0}.txt".format(config.project)
try:
    with open(gource_input_txt, "w", encoding='utf-8') as gource_file:
        gource_file.write("\n".join(gource_list))
    print("Gource input is saved in '{0}'".format(gource_input_txt))
except OSError:
    print("OSError while writing to file: " + gource_input_txt)
except KeyboardInterrupt:
    print("Interrupted by user. Stopping...")
except Exception as e:
    print("Unexpected exception", e)
    print("Bailing out")
