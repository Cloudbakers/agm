from agm import agm

first_command = {
    "command": ["drive", "files", "get"],
    "user": ["alex"],
    "zip": ["c", "d"],
    "two": ["a", "b"],
    "one": ["asdfasdf"],
}
single_arg = [first_command]
multiple_args = [first_command, first_command]


def test_single_arg():
    agm.get_list_of_requests(single_arg)


def test_multiple_args():
    agm.get_list_of_requests(multiple_args)
