import json

import pytest
from tornado.httpclient import HTTPRequest, HTTPResponse

from beer_garden.db.mongo.models import Garden
from beer_garden.db.schemas.garden_schema import GardenSchema


@pytest.fixture
def http_connection_params():
    return {
        "http": {
            "host": "somehost",
            "port": 10001,
            "url_prefix": "/",
            "ca_verify": False,
            "ssl": False,
        }
    }


@pytest.fixture
def stomp_connection_params():
    return {
        "stomp": {
            "host": "somehost",
            "port": 10001,
            "ssl": {"use_ssl": False},
            "headers": [],
            "send_destination": "sendtohere",
            "subscribe_destination": "listenhere",
            "username": "stompuser",
            "password": "stomppassword",
        }
    }


@pytest.fixture
def garden_with_http_connection_params(http_connection_params):
    garden = Garden(
        name="somehttpgardenname",
        connection_type="HTTP",
        connection_params=http_connection_params,
    ).save()

    yield garden

    garden.delete()


@pytest.fixture
def garden_with_stomp_connection_params(stomp_connection_params):
    garden = Garden(
        name="somestompgardenname",
        connection_type="STOMP",
        connection_params=stomp_connection_params,
    ).save()

    yield garden

    garden.delete()


class TestGardenConnections:
    @pytest.mark.parametrize(
        "garden, required_fields, endpoint",
        (
            (
                pytest.lazy_fixture("garden_with_http_connection_params"),
                {"host", "port", "url_prefix"},
                "http",
            ),
            (
                pytest.lazy_fixture("garden_with_stomp_connection_params"),
                {"host", "port"},
                "stomp",
            ),
        ),
    )
    @pytest.mark.gen_test
    def test_import_with_missing_required_params_returns_useful_message(
        self,
        garden,
        required_fields,
        endpoint,
        http_client,
        base_url,
    ):
        missing_data_message = "Missing data for required field."  # default marshmallow

        endpoint_connection_params = garden.connection_params.pop(endpoint)
        for required_field in required_fields:
            _ = endpoint_connection_params.pop(required_field)

        garden.connection_params = {endpoint: endpoint_connection_params}
        patch_request_body = f"""{{"operations": [
            {{
                "operation": "config",
                "value": {GardenSchema(strict=True).dumps(garden).data}
            }}
        ]}}
        """

        url = f"{base_url}/api/v1/gardens/" + garden.name
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        request = HTTPRequest(
            url, method="PATCH", headers=headers, body=patch_request_body
        )

        response: HTTPResponse
        response = yield http_client.fetch(request, raise_error=False)
        error_dict = json.loads(response.error.message.replace("'", '"'))[
            "connection_params"
        ][endpoint]

        for field in required_fields:
            assert field in error_dict
            assert error_dict[field].pop() == missing_data_message
