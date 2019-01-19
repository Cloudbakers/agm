import pytest
from agm import executor


@pytest.fixture
def sample_api_params():
    return {
        "service": "drive",
        "resources": ["files"],
        "method": "create",
        "version": "v3",
        "sample_field": "test",
        "name": "file1",
    }


def test_basic_parameters(sample_api_params):
    request = executor.GoogleAPIRequest(**sample_api_params)
    assert request.service == sample_api_params["service"]
    assert request.resources == sample_api_params["resources"]
    assert request.method == sample_api_params["method"]


def test_parameters(sample_api_params):
    request = executor.GoogleAPIRequest(**sample_api_params)
    assert request.parameters == {"sample_field": "test", "fields": "*"}


def test_body(sample_api_params):
    request = executor.GoogleAPIRequest(**sample_api_params)
    assert request.body["name"] == sample_api_params["name"]
