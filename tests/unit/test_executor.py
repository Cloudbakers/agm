import pytest
from agm import executor


sample_with_body = {
    "service": "drive",
    "resources": ["files"],
    "method": "create",
    "version": "v3",
    "sample_field": "test",
    "name": "file1",
}

sample_no_body = {
    "service": "drive",
    "resources": ["files"],
    "method": "get",
    "version": "v3",
    "sample_field": "test",
    "name": "file1",
}

samples = [sample_with_body, sample_no_body]


@pytest.mark.parametrize("sample_api_params", samples)
def test_basic_parameters(sample_api_params):
    request = executor.GoogleAPIRequest(**sample_api_params)
    assert request.service == sample_api_params["service"]
    assert request.resources == sample_api_params["resources"]
    assert request.method == sample_api_params["method"]


def test_parameters():
    request = executor.GoogleAPIRequest(**sample_with_body)
    assert request.parameters == {
        "sample_field": "test",
        "fields": "*",
        "body": {"name": "file1"},
    }
    request = executor.GoogleAPIRequest(**sample_no_body)
    assert request.parameters == {
        "name": "file1",
        "sample_field": "test",
        "fields": "*",
    }
