import copy
from contextlib import nullcontext as does_not_raise

import pytest
from mongoengine import connect

from beer_garden import config
from beer_garden.db.mongo.models import Garden
from beer_garden.db.schemas.garden_schema import GardenSchema
from beer_garden.garden import get_gardens

LOCAL_GARDEN_NAME = "localgarden"
REMOTE_GARDEN_NAME = "childgarden"
LOCAL_GARDEN_CONNECTION_TYPE = "LOCAL"
MANDATORY_HTTP_FIELDS = ["host", "port", "url_prefix"]
MANDATORY_STOMP_FIELDS = ["host", "port", "ssl"]


class TestGardenConnection:
    @pytest.fixture(autouse=True)
    def setup(self):
        config._CONFIG = {"garden": {"name": "localgarden"}}
        connect("beer_garden", host="mongomock://localhost")
        Garden.drop_collection()

    @pytest.fixture
    def good_http_params(self):
        return {
            "host": "gardenhost",
            "port": 2337,
            "url_prefix": "/",
            "ca_verify": False,
            "ssl": False,
        }

    @pytest.fixture
    def good_stomp_params(self):
        return {"host": "gardenhost", "port": 10119, "ssl": {"use_ssl": False}}

    @pytest.fixture
    def good_local_db_garden(self):
        garden = Garden(
            name=LOCAL_GARDEN_NAME, connection_type=LOCAL_GARDEN_CONNECTION_TYPE
        ).save()
        yield garden
        garden.delete()

    @pytest.fixture
    def bad_local_db_garden(self, good_http_params):
        garden = Garden(
            name=LOCAL_GARDEN_NAME,
            connection_type=LOCAL_GARDEN_CONNECTION_TYPE,
            connection_params={"http": good_http_params},
        ).save()
        assert garden.connection_params != {}  # i.e., it's "bad" in the DB
        yield garden
        garden.delete()

    @pytest.fixture
    def good_remote_http_db_garden(self, good_http_params):
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="HTTP",
            connection_params={"http": good_http_params},
        ).save()
        yield garden
        garden.delete()

    @pytest.fixture
    def good_remote_http_db_garden_empty_stomp(self, good_http_params):
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="HTTP",
            connection_params={"http": good_http_params, "stomp": {}},
        ).save()
        yield garden
        garden.delete()

    @pytest.fixture(params=MANDATORY_STOMP_FIELDS)
    def good_remote_http_db_garden_bad_stomp(
        self, request, good_http_params, good_stomp_params
    ):
        remove_field = request.param
        bad_stomp_params = copy.deepcopy(good_stomp_params)
        _ = bad_stomp_params.pop(remove_field)
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="HTTP",
            connection_params={"http": good_http_params, "stomp": bad_stomp_params},
        ).save(validate=False)
        yield garden
        garden.delete()

    @pytest.fixture(params=MANDATORY_HTTP_FIELDS)
    def bad_remote_http_db_garden_no_stomp(self, request, good_http_params):
        remove_field = request.param
        bad_http_params = copy.deepcopy(good_http_params)
        _ = bad_http_params.pop(remove_field)
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="HTTP",
            connection_params={"http": bad_http_params},
        ).save(validate=False)
        yield garden
        garden.delete()

    @pytest.fixture(params=MANDATORY_HTTP_FIELDS)
    def bad_remote_http_db_garden_good_stomp(
        self, request, good_http_params, good_stomp_params
    ):
        remove_field = request.param
        bad_http_params = copy.deepcopy(good_http_params)
        _ = bad_http_params.pop(remove_field)
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="HTTP",
            connection_params={"http": bad_http_params, "stomp": good_stomp_params},
        ).save(validate=False)
        yield garden
        garden.delete()

    @pytest.fixture(params=MANDATORY_HTTP_FIELDS)
    def bad_remote_http_db_garden_bad_stomp(
        self, request, good_http_params, good_stomp_params
    ):
        remove_field = request.param
        bad_http_params = copy.deepcopy(good_http_params)
        _ = bad_http_params.pop(remove_field)
        bad_stomp_params = copy.deepcopy(good_stomp_params)
        _ = bad_stomp_params.pop("host")
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="HTTP",
            connection_params={"http": bad_http_params, "stomp": bad_stomp_params},
        ).save(validate=False)
        yield garden
        garden.delete()

    @pytest.fixture
    def bad_remote_http_db_garden_no_http_no_stomp(self):
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="HTTP",
            connection_params={},
        ).save(validate=False)
        yield garden
        garden.delete()

    @pytest.fixture
    def bad_remote_http_db_garden_no_http_good_stomp(self, good_stomp_params):
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="HTTP",
            connection_params={"stomp": good_stomp_params},
        ).save(validate=False)
        yield garden
        garden.delete()

    @pytest.fixture(params=MANDATORY_STOMP_FIELDS)
    def bad_remote_http_db_garden_no_http_bad_stomp(self, request, good_stomp_params):
        remove_field = request.param
        bad_stomp_params = copy.deepcopy(good_stomp_params)
        _ = bad_stomp_params.pop(remove_field)
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="HTTP",
            connection_params={"stomp": bad_stomp_params},
        ).save(validate=False)
        yield garden
        garden.delete()

    @pytest.fixture
    def bad_remote_stomp_db_garden_no_http_no_stomp(self):
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="STOMP",
        ).save(validate=False)
        yield garden
        garden.delete()

    @pytest.fixture(params=MANDATORY_STOMP_FIELDS)
    def bad_remote_stomp_db_garden_no_http_bad_stomp(self, request, good_stomp_params):
        remove_field = request.param
        bad_stomp_params = copy.deepcopy(good_stomp_params)
        _ = bad_stomp_params.pop(remove_field)
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="STOMP",
            connection_params={"stomp": bad_stomp_params},
        ).save(validate=False)
        yield garden
        garden.delete()

    @pytest.fixture(params=MANDATORY_STOMP_FIELDS)
    def bad_remote_stomp_db_garden_good_http_bad_stomp(
        self, request, good_http_params, good_stomp_params
    ):
        remove_field = request.param
        bad_stomp_params = copy.deepcopy(good_stomp_params)
        _ = bad_stomp_params.pop(remove_field)
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="STOMP",
            connection_params={"http": good_http_params, "stomp": bad_stomp_params},
        ).save(validate=False)
        yield garden
        garden.delete()

    @pytest.fixture(params=zip(MANDATORY_HTTP_FIELDS, MANDATORY_STOMP_FIELDS))
    def bad_remote_stomp_db_garden_bad_http_bad_stomp(
        self, request, good_http_params, good_stomp_params
    ):
        remove_http_field, remove_stomp_field = request.param  # 1 of each suffices
        bad_http_params = copy.deepcopy(good_http_params)
        bad_stomp_params = copy.deepcopy(good_stomp_params)
        _ = bad_http_params.pop(remove_http_field)
        _ = bad_stomp_params.pop(remove_stomp_field)
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="STOMP",
            connection_params={"http": bad_http_params, "stomp": bad_stomp_params},
        ).save(validate=False)
        yield garden
        garden.delete()

    @pytest.fixture(params=MANDATORY_HTTP_FIELDS)
    def bad_remote_stomp_db_garden_bad_http_good_stomp(
        self, request, good_http_params, good_stomp_params
    ):
        remove_field = request.param
        bad_http_params = copy.deepcopy(good_http_params)
        _ = bad_http_params.pop(remove_field)
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="STOMP",
            connection_params={"http": bad_http_params, "stomp": good_stomp_params},
        ).save(validate=False)
        yield garden
        garden.delete()

    @pytest.fixture(params=MANDATORY_HTTP_FIELDS)
    def good_remote_stomp_db_garden_bad_http(
        self, request, good_http_params, good_stomp_params
    ):
        remove_field = request.param
        bad_http_params = copy.deepcopy(good_http_params)
        _ = bad_http_params.pop(remove_field)
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="STOMP",
            connection_params={"http": bad_http_params, "stomp": good_stomp_params},
        ).save(validate=False)
        yield garden
        garden.delete()

    @pytest.fixture
    def good_remote_stomp_db_garden_empty_http(self, good_stomp_params):
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="STOMP",
            connection_params={"http": {}, "stomp": good_stomp_params},
        ).save()
        yield garden
        garden.delete()

    @pytest.fixture
    def good_remote_stomp_db_garden(self, good_stomp_params):
        garden = Garden(
            name=REMOTE_GARDEN_NAME,
            connection_type="STOMP",
            connection_params={"stomp": good_stomp_params},
        ).save()
        yield garden
        garden.delete()

    def test_get_gardens_good_local_preserved(self, good_local_db_garden):
        """If the local garden is saved in the DB with no connection params, then
        it is retrieved by `get_gardens` with no changes."""
        local_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type == LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        assert local_garden_from_get_gardens.connection_params == {}

    def test_get_gardens_bad_local_cleaned(self, bad_local_db_garden):
        """On the off chance that the local garden somehow has connection params in
        the DB, they'll be cleaned when retrieving via `get_gardens`."""
        local_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type == LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        assert local_garden_from_get_gardens.connection_params == {}

    def test_get_gardens_good_http_remote_empty_stomp_stripped(
        self, good_local_db_garden, good_remote_http_db_garden_empty_stomp
    ):
        """If a remote garden with good http params and empty stomp params is fetched
        via `get_gardens`, the empty stomp params are removed."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        assert "stomp" not in remote_garden_from_get_gardens.connection_params

    def test_get_gardens_good_stomp_remote_empty_http_stripped(
        self, good_local_db_garden, good_remote_stomp_db_garden_empty_http
    ):
        """If a remote garden with good stomp params and empty http params is fetched
        via `get_gardens`, the empty http params are removed."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        assert remote_garden_from_get_gardens is not None
        assert "http" not in remote_garden_from_get_gardens.connection_params

    def test_get_gardens_good_http_remote_preserved(
        self, good_local_db_garden, good_remote_http_db_garden, good_http_params
    ):
        """If a remote garden with good http params and no stomp params is fetched via
        `get_gardens`, the good http params are unchanged and no stomp params are
        added.
        """
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        assert "http" in remote_garden_from_get_gardens.connection_params
        assert "stomp" not in remote_garden_from_get_gardens.connection_params
        assert (
            remote_garden_from_get_gardens.connection_params["http"] == good_http_params
        )

    def test_get_gardens_good_stomp_remote_preserved(
        self, good_local_db_garden, good_remote_stomp_db_garden, good_stomp_params
    ):
        """If a remote garden with good stomp params and no http params is fetched via
        `get_gardens`, the good stomp params are unchanged and no http params are
        added.
        """
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        assert "http" not in remote_garden_from_get_gardens.connection_params
        assert "stomp" in remote_garden_from_get_gardens.connection_params
        assert (
            remote_garden_from_get_gardens.connection_params["stomp"]
            == good_stomp_params
        )

    def test_get_gardens_bad_stomp_removed_from_good_http(
        self, good_local_db_garden, good_remote_http_db_garden_bad_stomp
    ):
        """If the database holds a Garden whose connection type is HTTP and whose
        connection parameters contain a good 'http' value but an unparseable 'stomp'
        value, `get_gardens` fetches the Garden with the stomp connection params
        removed."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        assert "stomp" not in remote_garden_from_get_gardens.connection_params

    def test_get_gardens_bad_http_removed_from_good_stomp(
        self, good_local_db_garden, good_remote_stomp_db_garden_bad_http
    ):
        """If the database holds a Garden whose connection type is STOMP and whose
        connection parameters contain a good 'stomp' value but an unparseable 'http'
        value, `get_gardens` fetches the Garden with the http connection params
        removed."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        assert "http" not in remote_garden_from_get_gardens.connection_params

    def test_get_gardens_type_http_bad_http_no_stomp(
        self, good_local_db_garden, bad_remote_http_db_garden_no_stomp
    ):
        """If the database holds a Garden whose connection type is HTTP and whose
        connection parameters contain an unparseable 'http' value and no 'stomp' value,
        `get_gardens` fetches the Garden with the http connection params corrected."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        schema = GardenSchema(strict=True)
        assert "http" in remote_garden_from_get_gardens.connection_params
        assert "stomp" not in remote_garden_from_get_gardens.connection_params
        with does_not_raise():
            data = schema.dump(remote_garden_from_get_gardens).data
            schema.validate(data)

    def test_get_gardens_type_http_bad_http_good_stomp(
        self,
        good_local_db_garden,
        bad_remote_http_db_garden_good_stomp,
        good_stomp_params,
    ):
        """If the database holds a Garden whose connection type is HTTP and whose
        connection parameters contain an unparseable 'http' value but a good 'stomp'
        value, `get_gardens` fetches the Garden with the http connection params
        corrected and the stomp params unchanged."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        schema = GardenSchema(strict=True)
        assert "http" in remote_garden_from_get_gardens.connection_params
        assert (
            "stomp" in remote_garden_from_get_gardens.connection_params
            and remote_garden_from_get_gardens.connection_params["stomp"]
            == good_stomp_params
        )
        with does_not_raise():
            data = schema.dump(remote_garden_from_get_gardens).data
            schema.validate(data)

    def test_get_gardens_type_http_bad_http_bad_stomp(
        self, good_local_db_garden, bad_remote_http_db_garden_bad_stomp
    ):
        """If the database holds a Garden whose connection type is HTTP and whose
        connection parameters contain an unparseable 'http' value and an unparseable
        'stomp' value, `get_gardens` fetches the Garden with the http connection params
        corrected and the stomp params removed."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        schema = GardenSchema(strict=True)
        assert "http" in remote_garden_from_get_gardens.connection_params
        assert "stomp" not in remote_garden_from_get_gardens.connection_params
        with does_not_raise():
            data = schema.dump(remote_garden_from_get_gardens).data
            schema.validate(data)

    def test_get_gardens_type_http_no_http_no_stomp(
        self, good_local_db_garden, bad_remote_http_db_garden_no_http_no_stomp
    ):
        """If the database holds a Garden whose connection type is HTTP and no
        connection parameters, `get_gardens` fetches the Garden with http connection
        params from safe defaults and no stomp params."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        schema = GardenSchema(strict=True)
        assert "http" in remote_garden_from_get_gardens.connection_params
        assert "stomp" not in remote_garden_from_get_gardens.connection_params
        with does_not_raise():
            data = schema.dump(remote_garden_from_get_gardens).data
            schema.validate(data)

    def test_get_gardens_type_http_no_http_good_stomp(
        self,
        good_local_db_garden,
        bad_remote_http_db_garden_no_http_good_stomp,
        good_stomp_params,
    ):
        """If the database holds a Garden whose connection type is HTTP and no 'http'
        connection parameters but good 'stomp' params, `get_gardens` fetches the Garden
        with http connection params from safe defaults and no change to the stomp
        params."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        schema = GardenSchema(strict=True)
        assert "http" in remote_garden_from_get_gardens.connection_params
        assert "stomp" in remote_garden_from_get_gardens.connection_params
        assert (
            remote_garden_from_get_gardens.connection_params["stomp"]
            == good_stomp_params
        )
        with does_not_raise():
            data = schema.dump(remote_garden_from_get_gardens).data
            schema.validate(data)

    def test_get_gardens_type_http_no_http_bad_stomp(
        self, good_local_db_garden, bad_remote_http_db_garden_no_http_bad_stomp
    ):
        """If the database holds a Garden whose connection type is HTTP and no 'http'
        connection parameters and bad 'stomp' params, `get_gardens` fetches the Garden
        with http connection params from safe defaults and no stomp params."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        schema = GardenSchema(strict=True)
        assert "http" in remote_garden_from_get_gardens.connection_params
        assert "stomp" not in remote_garden_from_get_gardens.connection_params
        with does_not_raise():
            data = schema.dump(remote_garden_from_get_gardens).data
            schema.validate(data)

    def test_get_gardens_type_stomp_bad_no_http_no_stomp(
        self,
        good_local_db_garden,
        bad_remote_stomp_db_garden_no_http_no_stomp,
    ):
        """If the database holds a Garden whose connection type is STOMP and no
        connection parameters, `get_gardens` fetches the Garden with connection type set
        to HTTP and http connection params from safe defaults and no stomp params."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        schema = GardenSchema(strict=True)
        assert "http" in remote_garden_from_get_gardens.connection_params
        assert "stomp" not in remote_garden_from_get_gardens.connection_params
        assert remote_garden_from_get_gardens.connection_type == "HTTP"
        with does_not_raise():
            data = schema.dump(remote_garden_from_get_gardens).data
            schema.validate(data)

    def test_get_gardens_type_stomp_no_http_bad_stomp(
        self, good_local_db_garden, bad_remote_stomp_db_garden_no_http_bad_stomp
    ):
        """If the database holds a Garden whose connection type is STOMP and no http
        params and bad stomp params, `get_gardens` fetches the Garden with connection
        type set to HTTP and http connection params from safe defaults and no stomp
        params."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        schema = GardenSchema(strict=True)
        assert "http" in remote_garden_from_get_gardens.connection_params
        assert "stomp" not in remote_garden_from_get_gardens.connection_params
        assert remote_garden_from_get_gardens.connection_type == "HTTP"
        with does_not_raise():
            data = schema.dump(remote_garden_from_get_gardens).data
            schema.validate(data)

    def test_get_gardens_type_stomp_good_http_bad_stomp(
        self,
        good_local_db_garden,
        bad_remote_stomp_db_garden_good_http_bad_stomp,
        good_http_params,
    ):
        """If the database holds a Garden whose connection type is STOMP and no http
        params and bad stomp params, `get_gardens` fetches the Garden with connection
        type set to HTTP, http connection params unchanged and no stomp params."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        assert "http" in remote_garden_from_get_gardens.connection_params
        assert "stomp" not in remote_garden_from_get_gardens.connection_params
        assert remote_garden_from_get_gardens.connection_type == "HTTP"
        assert (
            remote_garden_from_get_gardens.connection_params["http"] == good_http_params
        )

    def test_get_gardens_type_stomp_bad_http_bad_stomp(
        self, good_local_db_garden, bad_remote_stomp_db_garden_bad_http_bad_stomp
    ):
        """If the database holds a Garden whose connection type is STOMP and bad http
        params and bad stomp params, `get_gardens` fetches the Garden with connection
        type set to HTTP, http connection params from safe defaults and no stomp
        params."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        schema = GardenSchema(strict=True)
        assert "http" in remote_garden_from_get_gardens.connection_params
        assert "stomp" not in remote_garden_from_get_gardens.connection_params
        assert remote_garden_from_get_gardens.connection_type == "HTTP"
        with does_not_raise():
            data = schema.dump(remote_garden_from_get_gardens).data
            schema.validate(data)

    def test_get_gardens_type_stomp_bad_http_good_stomp(
        self, good_local_db_garden, bad_remote_stomp_db_garden_bad_http_good_stomp
    ):
        """If the database holds a Garden whose connectiontype is STOMP and bad http
        params and good stomp params, `get_gardens` fetches the Garden without changing
        the connection type, without altering the stomp params and no http params."""
        remote_garden_from_get_gardens = list(
            filter(
                lambda x: x.connection_type != LOCAL_GARDEN_CONNECTION_TYPE,
                get_gardens(),
            )
        ).pop()
        schema = GardenSchema(strict=True)
        assert "http" not in remote_garden_from_get_gardens.connection_params
        assert "stomp" in remote_garden_from_get_gardens.connection_params
        assert remote_garden_from_get_gardens.connection_type == "STOMP"
        with does_not_raise():
            data = schema.dump(remote_garden_from_get_gardens).data
            schema.validate(data)
