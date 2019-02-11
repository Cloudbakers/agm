import pytest
import json
from agm import agm


simple_args_list = ["drive", "files", "etc", "list", "-v", "--fakearg", "test_data"]
unknown_args_list = [
    "--long",
    "old",
    "-s",
    "b",
    "--list",
    "1",
    "2",
    "3",
    "--flag",
    "--flag2",
]
example_dicts = [{"a": 1, "b": "12", "long": "new"}]
piped_standard_json = json.dumps(example_dicts)
piped_jsonlines = "\n".join(json.dumps(i) for i in example_dicts)
piped_jsonlinesb = "\n".join(json.dumps(i, indent=2) for i in example_dicts)
piped_args_line_separated = "a\nb\nc"


class TestDriveMethod:
    def setup(self):
        self.arg_list = simple_args_list
        self.parsed_args, self.unknown = agm.parse_known_args(self.arg_list)

    def test_command(self):
        assert self.parsed_args.command == self.arg_list[0:4]

    def test_verbose(self):
        assert self.parsed_args.verbose

    def test_unknown(self):
        assert self.unknown == self.arg_list[-2:]


def test_load_json_string_returns_none():
    assert agm.load_json_string_if_possible(None) is None
    assert agm.load_json_string_if_possible(1) is None
    assert agm.load_json_string_if_possible("asdf") is None


def test_load_standard_json():
    assert agm.load_json_string_if_possible(piped_standard_json) == example_dicts


def test_load_jsonlines():
    assert agm.load_json_string_if_possible(piped_jsonlines) == example_dicts
    assert agm.load_json_string_if_possible(piped_jsonlinesb) == example_dicts


def test_body():
    body = {"name": "1"}
    api_options = {"body": [str(body)]}
    assert agm.process_body(api_options)["body"][0] == body


class TestUnknownArgs:
    def setup(self):
        self.test_args = unknown_args_list
        self.parsed_args = agm.parse_unknown_args(self.test_args)

    def test_long(self):
        assert self.parsed_args.long == ["old"]

    def test_short(self):
        assert self.parsed_args.s == ["b"]

    def test_list(self):
        assert self.parsed_args.list == ["1", "2", "3"]

    def test_flag(self):
        assert self.parsed_args.flag is True


@pytest.mark.skip  # TODO: Add this exception
def test_mismatch():
    stdin = ""
    argslist = ["comm", "--three", "1", "2", "3", "--two", "1", "2"]
    with pytest.raises(agm.InvalidCommandException):
        agm.parse_all_args(stdin, argslist)


class TestAllArgs:
    def setup(self):
        self.json_stdin = piped_standard_json
        self.line_stdin = piped_args_line_separated
        self.argslist = simple_args_list + unknown_args_list
        self.parsed_dict = agm.parse_all_args(self.json_stdin, self.argslist)
        return

    def test_overlap(self):
        print(self.parsed_dict)
        assert len(self.parsed_dict) == 1
        first = self.parsed_dict[0]
        assert first["a"] == [1]
        assert first["long"] == ["new"]
