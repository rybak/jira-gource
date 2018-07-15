import jira
from history_converter import convert_history
import config

gource_list = convert_history(jira.changes[config.project],
                              config.sections_extension)

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
