#!/usr/bin/env python
"""
The main module -- parses APIs and builds commands to be sent to executor.py to
be ran. Could be refactored / broken up
"""
import argparse
import ast
import json
import logging
import logging.handlers
import os
import re
import sys
from distutils.version import StrictVersion
import requests

import pkg_resources

from tqdm import tqdm

from . import docs, executor, google_auth, utils
from .exceptions import InvalidCommandException, InvalidAuthException

logger = logging.getLogger(__name__)

# TODO USE CONFIGURATION if I can think of a compelling use case
# https://stackoverflow.com/questions/7567642/where-to-put-a-configuration-file-in-python


def get_parser():
    parser = argparse.ArgumentParser(
        description=utils.LOGO
        + "\nversion: "
        + pkg_resources.require("agm")[0].version,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("-v", "--verbose", help="longer output", action="store_true")

    api = parser.add_argument_group(
        "API", "Call the Google API or get docs with agm [service] [resource] [method]"
    )
    api.add_argument(
        "command",
        help="The name of the service to call e.g. drive files list.",
        nargs="*",
    )

    api.add_argument(
        "-u", "--user", "--users", help="The impersonated user(s).", nargs="*"
    )
    api.add_argument("--outfile", help="Send output to a given file.")
    api.add_argument(
        "-d",
        "--docs",
        help="Open the documentation for this function.",
        action="store_true",
    )
    api.add_argument(
        "--version", help="specify api version, ie 'v2'. Optional", action="store_true"
    )
    api.add_argument(
        "--scopes",
        help="API scopes to give the key. Optional and usually unnecessary. "
        "If not specified, AGM will try all possible scopes that could authenticate "
        "a command until it finds one that works. You can drop everything before the "
        "last slash in the url, eg just use gmail.readonly",
        nargs="+",
    )
    api.add_argument(
        "--keyfile",
        help="Optional. specify the keyfile to authenticate with. By default, AGM"
        "looks for a .json file inside ~/.agm",
    )

    tools = parser.add_argument_group("Tools", "AGM tools")
    tools.add_argument("-V", help="AGM version", action="store_true")
    tools.add_argument(
        "--run_oauth",
        help="Authenticate an individual Google account and store the credentials."
        "Requires scopes and user to be set.",
        action="store_true",
    )
    tools.add_argument(
        "--noauth_local_webserver", help=argparse.SUPPRESS, action="store_true"
    )
    tools.add_argument(
        "--authinfo",
        help="Print information about authenticated keys",
        action="store_true",
    )
    return parser


def parse_known_args(args):
    parser = get_parser()
    return parser.parse_known_args(args)


def load_json_string_if_possible(input_string):
    """
    Parses input as a piped dictionary, if possible. Returns None otherwise.
    Tries standard json and jsonlines
    """
    output = None
    input_string = str(input_string)
    if input_string:
        try:
            output = json.loads(input_string)
            if isinstance(output, dict):
                output = [output]
            elif isinstance(output, list):
                pass
            else:
                output = None
        except Exception as e:  # TODO: specify exception
            lines = re.findall("[^}]+}", input_string)
            output = []
            for line in lines:
                try:
                    output.append(json.loads(line))
                except Exception as e:
                    return None
    return output or None


def parse_unknown_args(unknown):
    """
    Parse the "unknown" args -- ie, args that should be part of the api parameters.
    Everything is parsed as a list, and we will parse this further later.
    """
    api_parser = argparse.ArgumentParser()

    class EmptyIsTrue(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            if len(values) == 0:
                values = True
            setattr(namespace, self.dest, values)

    for arg in unknown:
        if arg.startswith(("-", "--")):
            api_parser.add_argument(arg, nargs="*", action=EmptyIsTrue)
    return api_parser.parse_args(unknown)


def process_body(api_options):
    if api_options.get("body"):
        api_options["body"] = [
            ast.literal_eval(item) for item in api_options["body"]
        ]  # TODO: Cleanup
    return api_options


def cli():  # MAIN
    argslist = sys.argv[1:]
    # TODO: Cleanup
    stdin = None
    if not sys.stdin.isatty():
        try:
            stdin = sys.stdin.read()
        except Exception as e:
            pass
    try:
        fully_parsed_args = parse_all_args(stdin, argslist)
        run(fully_parsed_args)
    except (InvalidCommandException, InvalidAuthException, argparse.ArgumentError) as e:
        if executor.GoogleAPIRequest.pbar:
            executor.GoogleAPIRequest.pbar.close()
        if logger.level == logging.DEBUG:
            logger.exception(e)
        print("ERROR: " + str(e))

    except Exception as e:
        print(
            "Unexpected error, please report to https://github.com/Cloudbakers/agm/issues"
        )
        raise e


def check_for_updates():
    local_version = pkg_resources.require("agm")[0].version
    url = "https://pypi.org/pypi/agm/json"
    remote_version = requests.get(url).json()["info"]["version"]
    if StrictVersion(remote_version) > StrictVersion(local_version):
        logger.warning(
            "WARNING: your build of AGM {} is out of date with the latest version {}. AGM is still in Alpha, so this may cause issues. Run pip install --upgrade agm to upgrade.".format(
                local_version, remote_version
            )
        )


def run(fully_parsed_args):
    args = fully_parsed_args[0]
    setup_logging(args.get("verbose"))
    logger.debug("Using options: {}".format(str(fully_parsed_args)))
    if args.get("V"):
        check_for_updates()
        print(pkg_resources.require("agm")[0].version)
        return
    elif args.get("authinfo"):
        google_auth.print_info()
        return
    elif args.get("run_oauth"):
        path = args.get("run_oauth")
        user = args.get("user")
        for item in ["scopes", "user"]:
            invalid = False
            if not args.get(item):
                print("Error! Please provide {}".format(item))
                invalid = True
        if invalid:
            return
        user = user[0]
        scopes = list(map(docs.parse_scopes, args.get("scopes")))
        google_auth.authenticate_client_secrets(
            scopes=scopes,
            user=user,
            noauth_local_webserver=args.get("noauth_local_webserver"),
        )
        return
    service, resource, method = docs.parse_command(
        args.get("command"), version=args.get("version")
    )
    if args.get("docs") or not method:
        docs.print_docs(service, resource, method)
        return
    scopes = (
        list(map(docs.parse_scopes, args.get("scopes") or [])) or method.get_scopes()
    )
    requests = get_list_of_requests(fully_parsed_args)
    executor.GoogleAPIRequest.pbar = tqdm(
        desc="progress",
        total=len(requests),
        unit="requests",
        smoothing=0.1,
        leave=False,
    )
    executor.multithread_execute_requests(requests, scopes=scopes)
    executor.GoogleAPIRequest.pbar.close()


# TODO: Cleanup
def get_list_of_requests(fully_parsed_args):
    """
    """
    # two paths -- list or dict
    request_list = []
    for request_cmd in fully_parsed_args:
        command = request_cmd["command"]
        service = command[0]
        outfile = request_cmd.get("outfile")
        version = request_cmd.get("version") or docs.get_preferred_version(service)
        reserved, _ = parse_known_args([])
        reserved = set(vars(reserved).keys()) - set(["user", "version"])
        nonreserved_params = {k: v for k, v in request_cmd.items() if k not in reserved}
        shared_params = {
            k: v[0]
            for k, v in nonreserved_params.items()
            if isinstance(v, list) and v is not None and len(v) == 1
        }
        tuple_list = [
            [(k, i) for i in v]
            for k, v in nonreserved_params.items()
            if isinstance(v, list) and v is not None and len(v) > 1
        ]
        if tuple_list:
            itr = zip(*tuple_list)
        else:
            itr = [()]
        for zipped in itr:
            parameters = {**dict(zipped), **shared_params}
            request_list.append(
                executor.GoogleAPIRequest(
                    service=service,
                    resources=command[1:-1],
                    method=command[-1],
                    version=version,
                    outfile=outfile,
                    **parameters,
                )
            )
    request_list.sort(key=lambda x: (x.user, x.version))
    return request_list


def parse_all_args(stdin, argslist):
    """
    """
    output = []
    all_options = {}
    if stdin:
        stdin = str(stdin)
    injson = load_json_string_if_possible(stdin)
    if stdin and not injson:
        argslist += stdin.splitlines()
    known, unknown = parse_known_args(argslist)
    all_options.update(vars(known))
    all_options.update(process_body(vars(parse_unknown_args(unknown))))
    if injson:
        for item in injson:
            for k, v in item.items():
                if not isinstance(v, list):
                    item[k] = [v]
            item.update(all_options)
        return injson
    else:
        output = [all_options]
    return output


class TqdmHandler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        tqdm.write(msg, file=sys.stderr)


def setup_logging(verbose):
    """
    Set up logging with the TQDM handler and a rotating file
    handler in ~/.agm
    """
    logfolder = os.path.join(utils.AGM_PATH, "logs")
    if not os.path.exists(logfolder):
        os.makedirs(logfolder)
    logfile = os.path.join(logfolder, "agm_logs.log")
    file_handler = logging.handlers.RotatingFileHandler(
        logfile, mode="a", maxBytes=10 ** 7, backupCount=5
    )  # Keep ~50MB of logs. Could make this configurable
    file_handler.setLevel(logging.DEBUG)
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.WARN
    logging.basicConfig(
        level=level,
        handlers=[TqdmHandler(), file_handler],
        format="%(asctime)s - %(name)s (%(lineno)s) - %(levelname)s: %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )
    logger.debug("Setting logging with verbose = {}".format(verbose))


if __name__ == "__main__":
    cli()
