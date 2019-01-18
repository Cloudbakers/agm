import json
import logging
import os
from argparse import Namespace

import apiclient.discovery
import httplib2
from oauth2client import tools
from oauth2client.client import HttpAccessTokenRefreshError, flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.service_account import ServiceAccountCredentials

from . import utils
from .exceptions import InvalidAuthException

logger = logging.getLogger(__name__)
logging.getLogger("googleapiclient").setLevel(logging.ERROR)
logging.getLogger("oauth2client").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)

services = {}
keyfile_directory = []


def get_service_account_keyfile():
    keyfiles = []
    for loc in utils.KEYFILE_PATHS:
        for file in os.listdir(loc):
            if (
                file.endswith(".json") and file != "client_secret.json"
            ):  # TODO check if it has keyfile in it, not just any json
                return os.path.join(loc, file)
    raise InvalidAuthException(
        "No keyfile found. "
        "Make sure to pass your keyfile as a parameter or add it to ~/.agm"
    )


DEFAULT_USER = "unnamed"
CREDS_FOLDER = os.path.join(utils.AGM_PATH, "oauth_credentials")
if not os.path.exists(CREDS_FOLDER):
    os.makedirs(CREDS_FOLDER)


def get_client_id():
    return


def authenticate_client_secrets(scopes, user=None, noauth_local_webserver=False):
    if not user:
        user = DEFAULT_USER
    creds_path = os.path.join(CREDS_FOLDER, "{}.json".format(user))  # DRY
    store = Storage(creds_path)
    client_secret = os.path.join(utils.AGM_PATH, "client_secret.json")
    if not os.path.exists(client_secret):
        print(
            "Error: No client secret file found. Download a client secret and put it in {}".format(
                client_secret
            )
        )
        return
    flow = flow_from_clientsecrets(client_secret, scopes)
    # We have to pass fake args here because it wants to be run as a CLI
    fake_args = Namespace(
        auth_host_name="localhost",
        noauth_local_webserver=noauth_local_webserver,
        auth_host_port=[8080, 8090],
        logging_level="ERROR",
    )
    credentials = tools.run_flow(flow=flow, storage=store, flags=fake_args)
    logger.info("Authenticated client secrets and stored in {}".format(utils.AGM_PATH))
    return credentials


def get_oauth_credentials(user):
    if not user:
        return None
    creds_path = os.path.join(CREDS_FOLDER, "{}.json".format(user))
    if os.path.exists(creds_path):
        return Storage(creds_path).get()
    else:
        logger.debug(
            "No oauth credentials found for {} in {}".format(user, utils.AGM_PATH)
        )
        return None


# TODO: rename variables. add docs
class Service:
    def __init__(
        self,
        service_name,
        version,
        scopes_to_try=None,
        keyfile=None,
        delegated_email=None,
        all_methods=None,
    ):
        self.name = service_name
        self.version = version
        self.keyfile = keyfile
        self.scopes_to_try = scopes_to_try
        self.delegated_email = delegated_email

    @classmethod
    def from_individual_oauth_key(cls, *args, **kwargs):
        cls.__init__(*args, **kwargs)
        # TBD
        return

    @classmethod
    def from_service_account_key(cls, *args, **kwargs):
        cls.__init__(*args, **kwargs)
        # TBD
        return

    def get_service_account_service(self):
        for scope in self.scopes_to_try:
            service = self.attempt_authorization(self.keyfile, scope)
            if service:
                return service

    def attempt_authorization(self, keyfile, scope):
        for_user = " for user {}".format(self.delegated_email)
        try:
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                keyfile, scope
            )
            debug_line = "Authorized {} with scope {}".format(keyfile, scope)
            # delegated permissions
            if self.delegated_email:
                credentials = credentials.create_delegated(self.delegated_email)
                debug_line += for_user
            http = credentials.authorize(http=httplib2.Http())
            service = apiclient.discovery.build(self.name, self.version, http=http)
            logger.debug(debug_line)
            return service
        except HttpAccessTokenRefreshError:
            debug_line = "Failed to authorize keyfile {} using scope {}".format(
                keyfile, scope
            )
            if self.delegated_email:
                debug_line += for_user
            logger.debug(debug_line)
            return None

    def get_available_scopes(self):
        # slow
        # print
        return

    def get_oauth_service(self, credentials):  # DRY
        http = credentials.authorize(http=httplib2.Http())
        service_auth = apiclient.discovery.build(
            self.name, self.version, http=http
        )  # ??
        return service_auth

    def build(self):
        oauth = get_oauth_credentials(self.delegated_email)
        if oauth:
            logger.debug(
                "Got service for {} using individual oauth".format(self.delegated_email)
            )
            return self.get_oauth_service(oauth)
        else:
            self.keyfile = get_service_account_keyfile()
            return self.get_service_account_service()


def print_info():  # colorize this and format it nice
    output = {}
    output["oauth_creds"] = []
    creds_path = CREDS_FOLDER
    for credsfile in os.listdir(creds_path):
        with open(os.path.join(CREDS_FOLDER, credsfile)) as f:
            creds_info = json.load(f)
            user = credsfile.split(".json")[0]
            output["oauth_creds"].append(
                {"user": user, "scopes": creds_info.get("scopes")}
            )

    output["service_accounts"] = []
    try:
        keyfile = get_service_account_keyfile()
    except InvalidAuthException:
        keyfile = None
    if keyfile:
        with open(keyfile) as f:
            key_info = json.load(f)
            project = key_info.get("project_id")
            if project:
                output["service_accounts"].append(
                    {"project": project, "client_id": key_info["client_id"]}
                )
    print(json.dumps(output, indent=2))
