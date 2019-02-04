# Test that an AGM command properly generates a list of requests
import pytest
from agm import agm, exceptions

stdin = None
valid1 = ["directory", "users", "list"]
invalid1 = ["directory", "users", "lisadfst"]
invalid2 = ["directory", "users", "list", "extra"]


valid = [valid1]
invalid = [invalid1, invalid2]


def test_valid():
    for argslist in valid:
        agm.get_list_of_requests(agm.parse_all_args(stdin, argslist))


def test_invalid():
    for argslist in invalid:
        with pytest.raises(exceptions.InvalidCommandException):
            agm.get_list_of_requests(agm.parse_all_args(stdin, argslist))
