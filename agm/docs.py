"""
This is a module for interacting with the discovery document.
It's wonky and messy, definitely room for improvement
"""
import os
import textwrap
from datetime import timedelta

import colorful
import requests
import requests_cache

from . import utils

colorful.use_style("solarized")
# Since the discovery document doesn't change often, I use a cache in order to
# Save time making calls to it.
# Warning! This will affect if you ever use the requests module elsewhere.

cache_path = os.path.join(utils.AGM_PATH, ".discovery_cache")
requests_cache.install_cache(cache_path, expire_after=timedelta(days=1))


def parse_scopes(name_or_url):
    """
    Allows for simpler specification of scopes instead of the full url
    """
    api_base_url = "https://www.googleapis.com/auth/"
    # This is the only exception I'm aware of
    gmail_url = "https://mail.google.com/"
    if name_or_url == "gmail" or name_or_url == gmail_url:
        name_or_url = "https://mail.google.com/"
    elif not name_or_url.startswith(api_base_url):
        name_or_url = api_base_url + name_or_url
    return name_or_url


def list_api_names_versions():
    result = requests.get(
        "https://www.googleapis.com/discovery/v1/apis",
        params={"fields": "items(name,version)"},
    )
    apis = result.json()["items"]
    return apis


def get_preferred_version(service_name):
    """ Get last nonbeta/nonalpha version, or earliest betas if its the only versions"""
    apis = [
        item for item in list_api_names_versions() if item.get("name") == service_name
    ]
    versions = [item.get("version") for item in apis]
    versions.sort(reverse=True)
    release_versions = [
        version
        for version in versions
        if ("alpha" not in version and "beta" not in version)
    ]
    if not release_versions:
        versions.reverse()
        return versions[0]
    else:
        return release_versions[0]


def print_apis():
    output_str = colorful.blue("Available APIs:")
    names = set()
    for api in list_api_names_versions():
        output_str += colorful.green("\n" + api.get("name") + " " + api.get("version"))
    print(output_str)


class ServiceDocumentation:
    def __init__(self, service, version=None):
        self.document = self.get_api_document(service, version)
        self.name = self.document["name"]
        self.version = self.document["version"]

    def get_all_scopes(self):
        return self.document["auth"]["oauth2"]["scopes"].keys()

    def get_api_document(self, api_name, version):
        # TODO: Retry logic
        # TODO: clean up a little
        # Admin APIs have a different naming scheme.
        if api_name in ["datatransfer", "directory", "reports"]:
            name = "admin"
            apis = list_api_names_versions()
            for api in apis:
                if api_name in api.get("version"):
                    version = api.get("version")
        else:
            name = api_name
            version = version or get_preferred_version(name)
        result = requests.get(
            "https://www.googleapis.com/discovery/v1/apis/{}/{}/rest".format(
                name, version
            )
        )
        return result.json()

    def get_item_docs(self, item, indent=0):
        # Recursive
        result_str = ""
        if not item.get("properties"):
            return ""
        for property, value in item.get("properties").items():
            result_str += item_definition(
                property, value.get("type"), value.get("description"), indent
            )
            sub_item = None
            if value.get("items"):
                if value["items"].get("$ref"):
                    sub_schema = value["items"]["$ref"]
                    sub_item = self.document["schemas"][sub_schema]
            elif value.get("properties"):
                sub_item = value.get("items")
            if sub_item:
                result_str += self.get_item_docs(sub_item, indent=indent + 2)
        return result_str

    def get_resources(self):
        if self.document.get("resources"):
            return self.document["resources"].keys()

    def get_schema(self, schema_name):
        return self.document["schemas"][schema_name]

    def __str__(self):
        out_str = ""
        title = self.document.get("title")
        version = self.document.get("version")
        out_str += colorful.bold_red("{} {}\n".format(title, version))
        out_str += self.document.get("description") + "\n\n"
        out_str += header("Resources: ")
        for resource in self.get_resources():
            out_str += colorful.green(resource) + "\n"
        return out_str


class ResourceDocumentation:
    def __init__(self, service, resource_names):
        """
        Wonky
        """
        self.resource_names = resource_names
        self.service = service
        self.document = self.get_resource_docs(resource_names)
        pass

    def get_resource_docs(self, resource_names):
        """ eg calendar users """
        nested_resource = self.service.document
        for resource in resource_names or []:
            child_resource = nested_resource.get("resources", {}).get(resource)
            if child_resource:
                self.name = resource
                nested_resource = child_resource
        resource = nested_resource
        return resource

    def get_resources(self):
        if self.document.get("resources"):
            return self.document["resources"].keys()
        return []

    def get_methods_string(self, indent=0):
        resource = self.document  # rename
        methods = resource.get("methods")
        methods_string = ""
        if methods:
            methods_string += colorful.blue("Methods:")
            for k, v in methods.items():
                method = (
                    "\n"
                    + colorful.green(k)
                    + ": "
                    + wrapped_text(v.get("description"), indent)
                )
                methods_string += method
        return methods_string

    def __str__(self):
        out_str = ""
        out_str += header("Resource {}".format(".".join(self.resource_names)))
        out_str += "\n"
        if self.get_resources():
            out_str += header("Resources: ")
            out_str += colorful.green("\n".join(self.get_resources()))
            out_str += "\n\n"
        out_str += self.get_methods_string()
        return out_str


class MethodDocumentation:
    def __init__(self, service, resource, method_name, version=None):
        self.service = service
        self.service_docs = service.document
        self.resource_docs = resource.document
        self.docs = self.resource_docs["methods"].get(
            method_name
        )  # TODO: rename to document
        if not self.docs:
            return
        self.name = self.docs["id"]
        self.scopes = self.docs.get("scopes")

    def get_scopes(self):
        return self.docs.get("scopes")

    def get_parameters(self):
        return self.a

    def get_request_body(self):
        request_body = self.docs.get("request")
        if request_body:
            schema = request_body.get("$ref")
            return self.service.get_schema(schema)

    def get_body_properties(self):
        body = self.get_request_body()
        if body:
            return body.get("properties")

    def __str__(self):
        out_str = header("Method: {}".format(self.name))
        out_str += self.docs.get("description")
        if self.docs.get("parameters"):
            out_str += "\n\n"
            out_str += header("Parameters:")
            for k, v in self.docs["parameters"].items():
                doc = item_definition(k, v["type"], v["description"])
                if v.get("required"):  # TODO: move these to be first
                    doc = colorful.red("(Required) ") + doc
                out_str += doc
        if self.get_request_body():
            out_str += header("\nRequest body:")
            out_str += self.service.get_item_docs(
                self.service.document, self.get_request_body()
            )
        if self.docs.get("response"):
            out_str += header("\nResult: ")
            out_str += self.service.get_item_docs(
                self.service.document["schemas"][self.docs.get("response")["$ref"]]
            )
        out_str += header("\nRequires one of these scopes:")
        out_str += "\n".join(self.docs.get("scopes"))
        return str(out_str)


def header(string):  # style a header
    return colorful.blue(string) + "\n"


def wrapped_text(string, indent=0):
    if not string:
        return ""
    lines = string.splitlines()
    result = ""
    result += textwrap.fill(lines[0], width=150, subsequent_indent=" " * (indent + 2))
    for line in lines[1:]:
        result += "\n"
        result += textwrap.fill(
            line,
            width=150,
            initial_indent=" " * (indent + 2),
            subsequent_indent=" " * (indent + 2),
        )
    return result


def item_definition(item, type, description, indent=0):
    a = " " * indent
    return a + "{}{}{} ({}{}{}): {}".format(
        colorful.green,
        item,
        colorful.reset,
        colorful.cyan,
        type,
        colorful.reset,
        wrapped_text(description, indent=indent) + "\n",
    )


def get_method_docs(
    service_name, resource_names, method_name, version=None
):  # awkward function
    service = ServiceDocumentation(service_name, version)
    resource = ResourceDocumentation(service, resource_names)
    method = MethodDocumentation(service, resource, method_name)
    return method


def parse_command(command, version=None):
    """
    Take a command and determine the service, resource and method
    """
    command_list = command
    service = None
    resource = None
    method = None
    if len(command_list) > 0:
        service_name = command_list[0]
        service = ServiceDocumentation(service_name, version)
    if len(command_list) > 1:
        resource = ResourceDocumentation(service, command_list[1:])
        if resource.name != command_list[-1]:
            method = MethodDocumentation(service, resource, command_list[-1])
    return service, resource, method


def print_docs(service, resource, method):
    # This is wonky
    if service and resource and method:
        print(method)
    elif service and resource:
        print(resource)
    elif service:
        print(service)
    else:
        print_apis()
