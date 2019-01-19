"""
A module for executing Google API requests --
by thread, by batch, and going through Individual pages.
"""
import time
import uuid
import json
import random
import logging
import concurrent.futures
import itertools
from socket import error as SocketError
from urllib3.exceptions import HTTPError
from . import google_auth, docs

NUM_RETRIES = 10

logger = logging.getLogger(__name__)


class GoogleAPIRequest:
    pbar = None

    def __init__(
        self,
        service,
        resources,
        method,
        version,
        user=None,
        outfile=None,
        output="json",
        *args,
        **kwargs
    ):
        self.service = service
        self.resources = resources
        self.method = method
        self.version = version
        self.user = user
        self.parameters = {"fields": "*"}
        self.parameters.update(dict(kwargs))
        if output == "json":
            self.callback = self.json_callback
        self.retry = False
        self.outfile = outfile
        self.retry_count = NUM_RETRIES
        self.parse_body()

    def parse_body(self):  # Slow?
        # TODO: maybe move this
        """
        We want to take the parameters that are part of the body and send them
        to the body, and parameters that are part of parameters to remain parameters
        """
        method_docs = docs.get_method_docs(
            self.service, self.resources, self.method, version=self.version
        )
        body_docs = method_docs.get_body_properties()
        body_data = {}
        new_parameters = {}
        if body_docs:
            body_params = set(body_docs.keys())
            for parameter, value in self.parameters.items():
                if parameter in body_params:
                    body_data[parameter] = value
                else:
                    new_parameters[parameter] = value
            self.parameters = new_parameters
            if body_data:
                self.parameters["body"] = body_data

    def get_batched_together(self):
        """
        Indicates the variables that mean that these requests can be executed
        with the same service
        """
        return (self.service, self.version, self.user)

    def get_request_info(self):
        """
        Used for printing the request
        """
        output = {}
        method = ".".join([self.service] + self.resources + [self.method])
        output["method"] = method
        output["parameters"] = self.parameters
        output["version"] = self.version
        output["user"] = self.user
        return output

    def json_callback(self, result):
        output = {}
        output["request"] = self.get_request_info()
        method = self.get_request_info()["method"]
        if isinstance(result, Exception):
            logger.warn("Failed request {}".format(method))
            output["response"] = {"error": str(result)}
        else:
            logger.debug("Executed request {}".format(method))
            output["response"] = result
        if self.outfile:
            with open(self.outfile, "a") as f:
                f.write(json.dumps(output, indent=3))
        else:
            outstring = json.dumps(output, indent=2)
            if self.pbar:
                self.pbar.write(outstring)
            else:
                print(outstring)
        if self.pbar:
            # Update TQDM progress bar
            if not output.get("response", {}).get("nextPageToken"):
                self.pbar.update(1)

    def __repr__(self):
        return str(self.get_request_info())


def multithread_execute_requests(request_list, scopes, keyfile=None, num_threads=5):
    """

    :param request_list: A list of GoogleAPIRequest objects to execute
    :param scopes: the scopes to give the service object for these requests
    :param num_threads: The number of threads to run. Default 5.
    :param keyfile: Optional. A keyfile to use if not pulled from ~/.agm
    """
    responses = []
    chunk_responses = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        request_futures = (
            executor.submit(
                execute_requests, list(chunk), *user_plus_version, keyfile, scopes
            )
            for user_plus_version, chunk in itertools.groupby(
                filter(None, request_list), lambda x: (x.get_batched_together())
            )
        )
        for future in concurrent.futures.as_completed(request_futures):
            chunk_responses += [future.result()]  # Doesnt actually return anything
    return responses


def execute_requests(requests, service, version, user, keyfile, scopes):
    """
    tbd
    """
    service = google_auth.Service(
        service_name=service,
        version=version,
        scopes_to_try=scopes,
        delegated_email=user,
        keyfile=keyfile,
    ).build()  # TODO: refactor a bit
    GOOGLE_API_RECOMMENDED_CHUNK_SIZE = 50
    requests_queue = iter(requests)
    all_responses = []
    retry_count = 10
    while 1:
        chunk = itertools.islice(requests_queue, GOOGLE_API_RECOMMENDED_CHUNK_SIZE)
        requests_chunk = list(chunk)
        logger.debug(
            "Executing {} requests for user {}".format(len(requests_chunk), user)
        )
        if len(requests_chunk) == 0:
            break
        for request in requests_chunk:
            if paged(service, request):
                execute_google_api_call_paged(service, request)
                request.executed = "paged"
            elif (
                "media_body" in request.parameters.keys()
            ):  # Cannot batch media uploads
                execute_single_api_call(service, request)
                request.executed = "single"
            else:
                request.executed = None
        requests_chunk = list(
            filter(lambda x: not x.executed, requests_chunk)
        )  # TODO test
        Batch(service, requests_chunk).execute()
        retries = list(filter(lambda x: x.retry and x.retry_count, requests_chunk))
        if len(retries) > 0:
            logger.debug(
                "retrying {} requests. saw error {}".format(
                    len(retries), retries[0].exception
                )
            )
        if retries:
            time.sleep(1 + random.random())
        requests_queue = itertools.chain(
            requests_queue, retries
        )  # Throw all retries to the end
    return 1


def paged(service, request):
    resource = _get_resource(service, request.resources)
    try:
        _ = getattr(resource, request.method + "_next")
        return True
    except AttributeError:
        # Then there is no "next" call associated with this method"
        return False


def execute_single_api_call(service, request):
    """
    For items that cannot batch
    """
    resource = _get_resource(service, request.resources)
    api_call = getattr(resource, request.method)(**request.parameters)
    try:
        result = api_call.execute(num_retries=NUM_RETRIES)
    except Exception as e:
        result = e
    request.callback(result)


def execute_google_api_call_paged(service, request):
    resource = _get_resource(service, request.resources)
    api_call = getattr(resource, request.method)(**request.parameters)
    while api_call is not None:
        try:
            result = api_call.execute(num_retries=NUM_RETRIES)
        except Exception as e:
            result = e
            request.callback(result)
            return
        request.callback(result)
        api_call = getattr(resource, request.method + "_next")(api_call, result)


def _get_resource(service, resources):
    """
    For multiple resources, give us the resource object associated with the
    last resource
    """
    resource = service
    for item in resources:
        resource = getattr(resource, item)()
    return resource


class Batch:
    def __init__(self, service, requests_chunk):
        self.requests = requests_chunk
        self.request_map = {}
        self.service = service
        return

    def execute(self):
        batch = self.service.new_batch_http_request(callback=self.batch_callback)
        for count, request in enumerate(self.requests):
            resource = _get_resource(self.service, request.resources)
            api_call = getattr(resource, request.method)(**request.parameters)
            request.request_id = str(count)
            batch.add(api_call, request_id=request.request_id)
            self.request_map[str(count)] = request
        n = 0
        while 1:  # Rare ConnectionErrors. Should be more specific
            try:
                return batch.execute()
            except (IOError, SocketError, HTTPError) as e:
                logger.error(e)
                time.sleep(2 ** n)
                n += 1
                if n == 5:
                    break

    def batch_callback(self, request_id, response, exception):
        request = self.request_map[request_id]
        if exception is not None:
            request.exception, retry = self.process_exception(exception, request)
            exception_dict, retry = self.process_exception(exception, request)
            if retry:
                request.retry = True
                request.retry_count -= 1
            if not retry:
                request.callback(exception)
            elif request.retry_count == 0:
                request.callback(exception)
        else:
            request.retry = False
            request.callback(response)

    def process_exception(self, exception, request):
        reasons_to_retry = [
            "userRateLimitExceeded",
            "quotaExceeded",
            "internalError",  # Sometimes shouldn't retry
            "rateLimitExceeded",
            "backendError",
            "transientError",
        ]
        try:
            content = json.loads(exception.content)
        except TypeError:  # Windows is different for some reason
            content = json.loads(exception.content.decode("utf-8"))
        except json.decoder.JSONDecodeError:
            content = exception.content.decode("utf-8")
        if isinstance(content, dict) and "errors" in content.get("error", {}).keys():
            error_reason = content["error"]["errors"][0]["reason"]
        else:
            error_reason = "No error reason given"
        # retry on user rate limit errors
        retry = error_reason in reasons_to_retry
        # if there is a request id, we need to set a new one
        if retry and "requestId" in request.parameters.keys():
            request_id = str(uuid.uuid4())
            request.parameters["requestId"] = request_id
        return content, retry
