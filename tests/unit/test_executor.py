import pytest
from agm import executor


@pytest.fixture
def sample_api_request():
    request = executor.GoogleAPIRequest(
        "service", ["a", "b"], "method", "v1", sample_field="test"
    )
    return request


def test_basic_parameters(sample_api_request):
    assert sample_api_request.service == "service"
    assert sample_api_request.resources == ["a", "b"]
    assert sample_api_request.method == "method"


def test_parameters(sample_api_request):
    assert sample_api_request.parameters == {"sample_field": "test", "fields": "*"}


def test_body():
    assert 1
