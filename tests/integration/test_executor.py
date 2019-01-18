import logging
from agm import executor

logging.basicConfig(level=logging.DEBUG)

get_request = executor.GoogleAPIRequest(
    service="drive",
    resources=["files"],
    method="get",
    version="v3",
    user="alexwennerberg@gmail.com",  # change this if you need to run integration tests
    fields="*",
    fileId="1CuShMuHuv3alIwqIPbKzeTFoZr2soesaBY5fa06nHlU",
)


def test_executor():
    request_list = [get_request] * 3
    scopes = ["https://www.googleapis.com/auth/drive"]
    list(executor.multithread_execute_requests(request_list, scopes=scopes))
    return
