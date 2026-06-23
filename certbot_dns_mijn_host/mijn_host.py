import json
import logging
import urllib.parse
from typing import Any, Callable, Optional

import requests
from certbot import errors
from certbot.plugins import dns_common
from certbot.plugins.dns_common import CredentialsConfiguration

logger = logging.getLogger(__name__)

BASE_URL = "https://mijn.host/api/v2/"


class Authenticator(dns_common.DNSAuthenticator):
    def __init__(self, *args, **kwargs):
        super(Authenticator, self).__init__(*args, **kwargs)
        self.credentials: Optional[CredentialsConfiguration] = None
        self.ttl = 60

    description = "This plugin configures a DNS TXT record to respond to a dns-01 challenge using the mijn.host API"

    @classmethod
    def add_parser_arguments(
        cls, add: Callable[..., None], default_propagation_seconds: int = 60
    ) -> None:
        super().add_parser_arguments(add, default_propagation_seconds)
        add("credentials", help="mijn.host credentials INI file.")

    def more_info(self) -> str:
        return "This plugin configures a DNS TXT record to respond to a dns-01 challenge using the mijn.host API."

    def _validate_credentials(self, credentials: CredentialsConfiguration) -> None:
        api_key = credentials.conf("api-key")
        if not api_key:
            raise errors.PluginError("No API key provided")

    def _setup_credentials(self) -> None:
        self.credentials = self._configure_credentials(
            "credentials",
            "mijn-host credentials INI file",
            None,
            self._validate_credentials,
        )

    def _perform(self, domain, validation_name, validation):
        self._get_mijn_host_client().add_txt_record(
            domain, validation_name, validation, self.ttl
        )

    def _cleanup(self, domain, validation_name, validation):
        self._get_mijn_host_client().del_txt_record(domain, validation_name, validation)

    def _get_mijn_host_client(self):
        if not self.credentials:
            raise errors.PluginError("Plugin not initialized")
        return MijnHostClient(self.credentials.conf("api-key"))


class MijnHostClientConnectionError(errors.PluginError):
    def __init__(self, response):
        self.status_code = response.status_code
        try:
            response_data = response.json()
        except json.decoder.JSONDecodeError:
            response_data = {}
        self.status_description = response_data.get("status_description")
        super().__init__(
            f"Received non-OK status from mijn.host API {self.status_code}: {self.status_description}"
        )


class MijnHostClient(object):
    def __init__(self, api_key):
        logger.debug("Creating MijnHostClient")
        self.headers = {
            "API-Key": api_key,
        }

    @staticmethod
    def _handle_response(
        resp: requests.Response, name: str = "something"
    ) -> tuple[int, Any]:
        if resp.status_code in (200, 400):
            try:
                return resp.status_code, resp.json()
            except json.decoder.JSONDecodeError:
                raise errors.PluginError(
                    f"API response for action '{name}' with non-json: {resp.text}"
                )
        else:
            raise MijnHostClientConnectionError(resp)

    def get_records(self, domain):
        url = urllib.parse.urljoin(BASE_URL, f"domains/{domain}/dns")
        req = requests.get(url, headers=self.headers)
        resp = self._handle_response(req, name="get records")
        return resp

    def update_records(self, domain, records):
        url = urllib.parse.urljoin(BASE_URL, f"domains/{domain}/dns")
        req = requests.put(
            url, headers=self.headers, data=json.dumps({"records": records})
        )
        resp = self._handle_response(req, name="update records")
        return resp

    def get_txt_records_and_base_domain(self, domain: str):
        for base_domain_guess in dns_common.base_domain_name_guesses(domain):
            response = self.get_records(base_domain_guess)
            if response[0] == 200:
                records = response[1].get("data", {}).get("records", [])
                base_domain = base_domain_guess
                return records, base_domain
            if response[0] == 400:
                if (
                    response[1].get("status_description", {})
                    != "You have no access to this resource."
                ):
                    raise errors.PluginError(
                        f"There is a problem with the mijn.host API request: {response[0]}, {response[1]}"
                    )
                else:
                    # Expected scenario if we have a subdomain
                    continue
        else:
            raise errors.PluginError(
                "API key does not provide access to requested domain"
            )

    def add_txt_record(
        self, domain: str, record_name: str, record_content: str, ttl: int
    ):
        records, base_domain = self.get_txt_records_and_base_domain(domain)
        new_record = {
            "type": "TXT",
            "name": record_name + ".",
            "value": record_content,
            "ttl": ttl,
        }

        if new_record in records:
            return

        records.append(new_record)
        self.update_records(base_domain, records)

    def del_txt_record(
        self, domain: str, record_name: str, record_content: str
    ) -> None:
        records, base_domain = self.get_txt_records_and_base_domain(domain)
        records_list = [
            r
            for r in records
            if not (
                r["type"] == "TXT"
                and r["name"] == record_name + "."
                and r["value"] == record_content
            )
        ]
        self.update_records(base_domain, records_list)
