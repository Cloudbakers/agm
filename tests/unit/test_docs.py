from agm import docs

# TODO: maybe test *all* commands with these tests?


def parse_method(command):
    command[-1] = ".".join(command)
    return command


def test_service_only():
    command = ["drive"]
    result = docs.parse_command(command)
    assert result[0].name == "drive"
    assert not any(result[1:])


def test_resource_only():
    command = ["drive", "files"]
    result = docs.parse_command(command)
    assert result[0].name == "drive"
    assert result[1].name == "files"
    assert not result[2]


def test_parse_commands():
    command = ["drive", "files", "list"]
    result = docs.parse_command(command)
    assert list(map(lambda x: x.name, result)) == parse_method(command)


def test_parse_complex_command():
    command = ["gmail", "users", "messages", "send"]
    result = docs.parse_command(command)
    parsed = parse_method(command)
    del parsed[1]
    assert list(map(lambda x: x.name, result)) == parsed


def test_method():
    command = ["drive", "files", "list"]
    result = docs.parse_command(command)
    assert result[2]


def test_parse_scopes():
    assert docs.parse_scopes("gmail") == "https://mail.google.com/"
    assert docs.parse_scopes("https://mail.google.com/") == "https://mail.google.com/"
    assert docs.parse_scopes("drive") == "https://www.googleapis.com/auth/drive"
    assert (
        docs.parse_scopes("https://www.googleapis.com/auth/drive")
        == "https://www.googleapis.com/auth/drive"
    )
