## Build deep hierarchy by fixVersion

In the `config.sample-hierarchy.apache-zeppeline.py` present an alternative configuration with some additional methods to build tiket issue path with all previous fix versions.

### How it work

Task `PROJECT-1` with the first fix version `1.0` will have path `PROJECT/1.0/PROJECT-1.Task` and all other tickets with that version also have that path (except the latest part), so all tiket will be group nearly
Another ticket with version `1.1` will include path from previous version, so Task `PROJECT-100` with this version will have path: `PROJECT/1.0/1.1/PROJECT-100.Task`
For the next version everything will work the same: `1.0/1.2/1.3/2.0/3.0/3.1`, but hotfix version (this a version with the third non-zero part like `1.0.1` will use parent part, but dont affect the whole hiearchy, will be like side branch as `0.6.2` in the picture bellow)

So we have a long chain of version and long history/graphic :) on the screen like
![sample of long chain](https://github.com/igubanov/jira-gource/assets/133564049/88d96a98-ba77-4e10-be90-7bc767a77a28)
and even longer.

### How it use

You should copy `config.sample-hierarchy.apache-zeppeline.py` to `config.py` and replace value for the next variables:

- `jira_url`
- `jira_server_project`
- `projects`
- `my_user_name`

and execute script

```
python -m pip install -r requirements.txt
python generate_gource.py
```

### Some tips for generate

A history line builded for project may be very long, by default gource show all folder/path/files on the screen make zoom is small, by prevent this action we can use combination of parameters `--camera-mode track` to keep focus on users (they are ussually near latest version) and `--padding 1.9` to have more space near the users (that's a workaround for zoom)

### Demo

This demo is builded from Appache/Zeppelin [public jira](https://issues.apache.org/jira/projects/ZEPPELIN/issues)
with the next generation's parameters:

```
gource -1280x720 -c 2 -s 1 --start-date "2019-01-01" --stop-date "2019-03-01" --hide filenames --user-image-dir user_image_dir --camera-mode track --key --padding 1.9 -o - gource-input.txt
```

https://github.com/igubanov/jira-gource/assets/133564049/a1f4ea32-5ce3-4750-8b84-ce1cde4e3fed
