import unittest
from unittest.mock import patch, MagicMock, call
import requests
import urllib

import json
from certbot import errors
from certbot_dns_mijn_host.mijn_host import MijnHostClient


BASE_URL = "https://mijn.host/api/v2/"


class TestMijnHostClient(unittest.TestCase):
    def setUp(self):
        self.api_key = "test-api-key"
        self.client = MijnHostClient(api_key=self.api_key)
        self.domain = "example.com"
        self.headers = {
            "API-Key": self.api_key,
        }

    @patch("requests.get")
    def test_get_records(self, mock_get):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"records": []}}
        mock_get.return_value = mock_response

        records = self.client.get_records(self.domain)

        mock_get.assert_called_once_with(
            urllib.parse.urljoin(BASE_URL, f"domains/{self.domain}/dns"),
            headers=self.headers,
        )
        self.assertEqual(records[0], 200)
        self.assertEqual(records[1], {"data": {"records": []}})

    @patch("requests.put")
    @patch("requests.get")
    def test_add_txt_record(self, mock_get, mock_put):
        mock_get_response = MagicMock(spec=requests.Response)
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"data": {"records": []}}
        mock_get.return_value = mock_get_response

        mock_put_response = MagicMock(spec=requests.Response)
        mock_put_response.status_code = 200
        mock_put_response.json.return_value = {"success": True}
        mock_put.return_value = mock_put_response

        self.client.add_txt_record(self.domain, "test", "test_content", 3600)

        expected_records = [
            {
                "type": "TXT",
                "name": "test.",
                "value": "test_content",
                "ttl": 3600,
            }
        ]

        mock_put.assert_called_once_with(
            urllib.parse.urljoin(BASE_URL, f"domains/{self.domain}/dns"),
            headers=self.headers,
            data=json.dumps({"records": expected_records}),
        )

    @patch("requests.put")
    @patch("requests.get")
    def test_del_txt_record(self, mock_get, mock_put):
        mock_get_response = MagicMock(spec=requests.Response)
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "data": {
                "records": [
                    {
                        "type": "TXT",
                        "name": "test.",
                        "value": "test_content",
                        "ttl": 3600,
                    }
                ]
            }
        }
        mock_get.return_value = mock_get_response

        mock_put_response = MagicMock(spec=requests.Response)
        mock_put_response.status_code = 200
        mock_put.return_value = mock_put_response

        self.client.del_txt_record(self.domain, "test", "test_content")

        mock_put.assert_called_once_with(
            urllib.parse.urljoin(BASE_URL, f"domains/{self.domain}/dns"),
            headers=self.headers,
            data=json.dumps({"records": []}),
        )

    @patch("requests.get")
    def test_handle_response_non_ok_status(self, mock_get):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        with self.assertRaises(errors.PluginError):
            self.client.get_records(self.domain)

    @patch("requests.get")
    def test_handle_response_non_json(self, mock_get):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.text = "Non-JSON Response"
        mock_response.json.side_effect = json.decoder.JSONDecodeError(
            "Expecting value", "doc", 0
        )
        mock_get.return_value = mock_response

        with self.assertRaises(errors.PluginError):
            self.client.get_records(self.domain)

    @patch("requests.get")
    def test_handle_response_error_exception(self, mock_get):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "status": 401,
            "status_description": "No valid API key set",
        }
        mock_get.return_value = mock_response

        with self.assertRaises(errors.PluginError):
            self.client.get_records(self.domain)

    @patch("requests.put")
    @patch("requests.get")
    def test_add_txt_record_with_subdomain(self, mock_get, mock_put):
        sub_domain_get_response = MagicMock(spec=requests.Response)
        sub_domain_get_response.status_code = 400
        sub_domain_get_response.json.return_value = {
            "status": 400,
            "status_description": "You have no access to this resource.",
        }

        base_domain_get_response = MagicMock(spec=requests.Response)
        base_domain_get_response.status_code = 200
        base_domain_get_response.json.return_value = {"data": {"records": []}}
        mock_get.side_effect = [sub_domain_get_response, base_domain_get_response]

        mock_put_response = MagicMock(spec=requests.Response)
        mock_put_response.status_code = 200
        mock_put_response.json.return_value = {"success": True}
        mock_put.return_value = mock_put_response

        base_domain = "example.com"
        sub_domain = "sub.example.com"

        self.client.add_txt_record(sub_domain, "test", "test_content", 3600)

        self.assertEqual(mock_get.call_count, 2)
        get_calls = mock_get.call_args_list
        self.assertEqual(
            get_calls[0],
            call(
                urllib.parse.urljoin(BASE_URL, f"domains/{sub_domain}/dns"),
                headers=self.headers,
            ),
        )
        self.assertEqual(
            get_calls[1],
            call(
                urllib.parse.urljoin(BASE_URL, f"domains/{base_domain}/dns"),
                headers=self.headers,
            ),
        )

        expected_records = [
            {
                "type": "TXT",
                "name": "test.",
                "value": "test_content",
                "ttl": 3600,
            }
        ]

        mock_put.assert_called_once_with(
            urllib.parse.urljoin(BASE_URL, f"domains/{base_domain}/dns"),
            headers=self.headers,
            data=json.dumps({"records": expected_records}),
        )

    @patch("requests.put")
    @patch("requests.get")
    def test_del_txt_record_with_subdomains(self, mock_get, mock_put):
        sub_domain_get_response = MagicMock(spec=requests.Response)
        sub_domain_get_response.status_code = 400
        sub_domain_get_response.json.return_value = {
            "status": 400,
            "status_description": "You have no access to this resource.",
        }

        base_domain_get_response = MagicMock(spec=requests.Response)
        base_domain_get_response.status_code = 200
        base_domain_get_response.json.return_value = {
            "data": {
                "records": [
                    {
                        "type": "TXT",
                        "name": "test.",
                        "value": "test_content",
                        "ttl": 3600,
                    }
                ]
            }
        }
        mock_get.side_effect = [sub_domain_get_response, base_domain_get_response]

        mock_put_response = MagicMock(spec=requests.Response)
        mock_put_response.status_code = 200
        mock_put.return_value = mock_put_response

        base_domain = self.domain
        sub_domain = "sub.example.com"

        self.client.del_txt_record(sub_domain, "test", "test_content")

        self.assertEqual(mock_get.call_count, 2)
        get_calls = mock_get.call_args_list
        self.assertEqual(
            get_calls[0],
            call(
                urllib.parse.urljoin(BASE_URL, f"domains/{sub_domain}/dns"),
                headers=self.headers,
            ),
        )
        self.assertEqual(
            get_calls[1],
            call(
                urllib.parse.urljoin(BASE_URL, f"domains/{base_domain}/dns"),
                headers=self.headers,
            ),
        )

        mock_put.assert_called_once_with(
            urllib.parse.urljoin(BASE_URL, f"domains/{base_domain}/dns"),
            headers=self.headers,
            data=json.dumps({"records": []}),
        )

    @patch("requests.get")
    def test_handle_response_unauthorized_subdomain(self, mock_get):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "status": 400,
            "status_description": "You have no access to this resource.",
        }
        mock_get.return_value = mock_response

        top_level_domain = "com"
        base_domain = "example.com"
        sub_domain = "sub.example.com"

        with self.assertRaises(errors.PluginError) as e:
            self.client.add_txt_record(sub_domain, "test", "test_content", 3600)

        exception = e.exception
        self.assertEqual(
            exception.args[0], "API key does not provide access to requested domain"
        )

        self.assertEqual(mock_get.call_count, 3)
        get_calls = mock_get.call_args_list
        self.assertEqual(
            get_calls[0],
            call(
                urllib.parse.urljoin(BASE_URL, f"domains/{sub_domain}/dns"),
                headers=self.headers,
            ),
        )
        self.assertEqual(
            get_calls[1],
            call(
                urllib.parse.urljoin(BASE_URL, f"domains/{base_domain}/dns"),
                headers=self.headers,
            ),
        )
        self.assertEqual(
            get_calls[2],
            call(
                urllib.parse.urljoin(BASE_URL, f"domains/{top_level_domain}/dns"),
                headers=self.headers,
            ),
        )

    @patch("requests.get")
    def test_handle_response_request_invalid(self, mock_get):
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "status": 400,
            "status_description": "Invalid input",
        }
        mock_get.return_value = mock_response

        sub_domain = "sub.example.com"

        with self.assertRaises(errors.PluginError) as e:
            self.client.add_txt_record(sub_domain, "test", "test_content", 3600)

        exception = e.exception
        self.assertEqual(
            exception.args[0],
            "There is a problem with the mijn.host API request: 400, {'status': 400, 'status_description': 'Invalid input'}",
        )

        self.assertEqual(mock_get.call_count, 1)
        get_calls = mock_get.call_args_list
        self.assertEqual(
            get_calls[0],
            call(
                urllib.parse.urljoin(BASE_URL, f"domains/{sub_domain}/dns"),
                headers=self.headers,
            ),
        )


if __name__ == "__main__":
    unittest.main()
