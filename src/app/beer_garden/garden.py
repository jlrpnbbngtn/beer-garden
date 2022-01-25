# -*- coding: utf-8 -*-
"""Garden Service

The garden service is responsible for:

* Generating local `Garden` record
* Getting `Garden` objects from the database
* Updating `Garden` objects in the database
* Responding to `Garden` sync requests and forwarding request to children
* Handling `Garden` events
"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple, Union

from brewtils.errors import PluginError
from brewtils.models import Event as BrewtilsEvent
from brewtils.models import Events as BrewtilsEvents
from brewtils.models import Garden as BrewtilsGarden
from brewtils.models import Operation as BrewtilsOperation
from brewtils.models import System as BrewtilsSystem
from brewtils.specification import _CONNECTION_SPEC
from marshmallow import ValidationError as MarshmallowValidationError
from mongoengine import DoesNotExist
from yapconf import YapconfSpec

import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.db.mongo.models import MongoModel
from beer_garden.db.schemas.garden_schema import (
    HttpConnectionParamsSchema,
    StompConnectionParamsSchema,
)
from beer_garden.events import publish, publish_event
from beer_garden.namespace import get_namespaces
from beer_garden.systems import get_systems, remove_system

logger = logging.getLogger(__name__)


def get_garden(garden_name: str) -> BrewtilsGarden:
    """Retrieve an individual Garden

    Args:
        garden_name: The name of the Garden

    Returns:
        The Garden

    """
    if garden_name == config.get("garden.name"):
        return local_garden()

    return clean_garden_connection_params(
        db.query_unique(BrewtilsGarden, name=garden_name, raise_missing=True)
    )


def get_gardens(include_local: bool = True) -> List[BrewtilsGarden]:
    """Retrieve list of all Gardens

    Args:
        include_local: Also include the local garden

    Returns:
        All known gardens

    """
    # This is necessary for as long as local_garden is still needed. See the notes
    # there for more detail.
    gardens = list(
        map(
            clean_garden_connection_params,
            db.query(BrewtilsGarden, filter_params={"connection_type__ne": "LOCAL"}),
        )
    )

    if include_local:
        gardens += [local_garden()]

    return gardens


def local_garden(all_systems: bool = False) -> BrewtilsGarden:
    """Get the local garden definition

    Args:
        all_systems: If False, only include "local" systems in the garden systems list

    Returns:
        The local Garden
    """
    # This function is still necessary because there are various things that expect
    # the system information to be embedded in the garden document itself (as opposed
    # Systems just having a reference to their garden). There is nothing that would
    # keep a LOCAL garden's embedded list of systems up to date currently, so we instead
    # build the list of systems (and namespaces) at call time. Once the System
    # relationship has been refactored, the need for this function should go away.
    garden: BrewtilsGarden = clean_garden_connection_params(
        db.query_unique(BrewtilsGarden, connection_type="LOCAL")
    )

    filter_params = {}
    if not all_systems:
        filter_params["local"] = True

    garden.systems = get_systems(filter_params=filter_params)
    garden.namespaces = get_namespaces()

    return garden


@publish_event(BrewtilsEvents.GARDEN_SYNC)
def publish_garden(status: str = "RUNNING") -> BrewtilsGarden:
    """Get the local garden, publishing a GARDEN_SYNC event

    Args:
        status: The garden status

    Returns:
        The local garden, all systems
    """
    garden = local_garden(all_systems=True)
    garden.connection_type = None
    garden.status = status

    return garden


def update_garden_config(garden: BrewtilsGarden) -> BrewtilsGarden:
    """Update Garden configuration parameters

    Args:
        garden: The Garden to Update

    Returns:
        The Garden updated

    """
    db_garden = db.query_unique(BrewtilsGarden, id=garden.id)
    db_garden.connection_params = garden.connection_params
    db_garden.connection_type = garden.connection_type
    db_garden.status = "INITIALIZING"

    return update_garden(db_garden)


def update_garden_status(garden_name: str, new_status: str) -> BrewtilsGarden:
    """Update an Garden status.

    Will also update the status_info heartbeat.

    Args:
        garden_name: The Garden Name
        new_status: The new status

    Returns:
        The updated Garden
    """
    garden = db.query_unique(BrewtilsGarden, name=garden_name)
    garden.status = new_status
    garden.status_info["heartbeat"] = datetime.utcnow()

    return update_garden(garden)


@publish_event(BrewtilsEvents.GARDEN_REMOVED)
def remove_garden(garden_name: str) -> None:
    """Remove a garden

    Args:
        garden_name: The Garden name

    Returns:
        The deleted garden
    """
    garden = get_garden(garden_name)

    # TODO: Switch to lookup by garden_name rather than namespace
    systems = get_systems(filter_params={"namespace": garden_name})

    for system in systems:
        remove_system(system.id)

    db.delete(garden)

    return garden


def get_connection_defaults():
    # Explicitly load default config options into garden params
    spec = YapconfSpec(_CONNECTION_SPEC)
    # bg_host is required to load brewtils garden spec
    defaults = spec.load_config({"bg_host": ""})

    config_map = {
        "bg_host": "host",
        "bg_port": "port",
        "ssl_enabled": "ssl",
        "bg_url_prefix": "url_prefix",
        "ca_cert": "ca_cert",
        "ca_verify": "ca_verify",
        "client_cert": "client_cert",
    }

    # TODO: this is a temporary work-around until Brewtils is configured to provide
    # sensible defaults
    bad_defaults = {"ssl_enabled", "ca_verify"}
    sensible_defaults = {
        "bg_host": "child_hostname",
        "bg_port": 1025,
        "ssl_enabled": False,
        "bg_url_prefix": "/",
        "ca_verify": False,
    }

    # substitute the sensible default only if we're provided `None` or an empty string
    new_defaults = {}
    for key in defaults:
        # setting ssl and ca_verify to `True` by default makes no sense
        if key in bad_defaults:
            new_defaults[key] = sensible_defaults[key]
        else:
            provided = defaults[key]
            if key in config_map:
                if provided is not None and provided:
                    # always use a string that is not empty
                    new_defaults[key] = provided
                else:
                    # but use the empty string if we don't provide an alternative
                    new_defaults[key] = (
                        sensible_defaults[key] if key in sensible_defaults else ""
                    )

    return new_defaults


def _create_basic_connection_defaults():
    config_map = {
        "bg_host": "host",
        "bg_port": "port",
        "ssl_enabled": "ssl",
        "bg_url_prefix": "url_prefix",
        "ca_cert": "ca_cert",
        "ca_verify": "ca_verify",
        "client_cert": "client_cert",
    }
    defaults = get_connection_defaults()

    return {config_map[key]: defaults[key] for key in config_map}


def _validate_http_connection_params(conn_params):
    return HttpConnectionParamsSchema(strict=True).load(conn_params).data


def _validate_stomp_connection_params(conn_params):
    return StompConnectionParamsSchema(strict=True).load(conn_params).data


def _clean_or_default_http_connection_params(
    params: Optional[dict], garden_name: str
) -> Tuple[dict, List[str]]:
    messages = []

    if params is None:
        params = _create_basic_connection_defaults()
        messages.append(
            "Used defaults for all values of http connection params "
            f"for garden {garden_name}"
        )
    else:
        try:
            params = _validate_http_connection_params(params)
        except MarshmallowValidationError:
            # something's wrong with these http conn params; try to salvage some of them
            try:
                params = _validate_http_connection_params(
                    {
                        **_create_basic_connection_defaults(),
                        **params,
                    }
                )
                messages.append(
                    "Used defaults for some values of http connection params "
                    f"for garden {garden_name}"
                )
            except MarshmallowValidationError:
                # can't salvage, so give it defaults rather than completely fail
                params = _create_basic_connection_defaults()
                messages.append(
                    "Used defaults for all values of http connection params "
                    f"for garden {garden_name}"
                )

    return params, messages


def _clean_or_empty_http_connection_params(
    params: Optional[dict], garden_name: str
) -> Tuple[dict, List[str]]:
    messages = []

    if params is None:
        params = {}
    else:
        try:
            params = _validate_http_connection_params(params)
        except MarshmallowValidationError:
            params = {}
            messages.append(
                f"Unable to parse http connection params for garden {garden_name}"
            )
    return params, messages


def _clean_or_empty_stomp_connection_params(
    params: Optional[dict], garden_name: str
) -> Tuple[dict, List[str]]:
    messages = []

    if params is None:
        params = {}
        messages.append(f"No stomp connection params provided for garden {garden_name}")
    else:
        try:
            params = _validate_stomp_connection_params(params)
        except MarshmallowValidationError:
            params = {}
            messages.append(
                "Unable to parse stomp connection params for garden " f"{garden_name}"
            )

    return params, messages


def clean_garden_connection_params(
    garden: Optional[Union[BrewtilsGarden, MongoModel]]
) -> Optional[Union[BrewtilsGarden, MongoModel]]:
    """Return a Garden with its connection parameters sanitized.

    If a Garden (as either a Brewtils model or a Mongo model) is passed that has
    connection parameters that will fail validation, those parameters are replaced by
    ones that won't.

    Args:
        garden: The Garden to clean

    Returns:
        The Garden with cleaned connection parameters
    """
    if garden is None:
        return garden

    messages = []
    conn_params = (
        garden.connection_params if hasattr(garden, "connection_params") else {}
    ) or {}

    if garden.connection_type is not None and garden.connection_type == "LOCAL":
        if conn_params != {}:
            logger.debug("Removed connection params for local garden")
            garden.connection_params = {}
        return garden

    garden_name = garden.name
    new_stomp_params, stomp_msgs = _clean_or_empty_stomp_connection_params(
        conn_params.get("stomp", None), garden_name
    )

    if garden.connection_type == "HTTP":
        new_http_params, http_msgs = _clean_or_default_http_connection_params(
            conn_params.get("http", None), garden_name
        )
        conn_params["http"] = new_http_params

        if new_stomp_params != {}:
            conn_params["stomp"] = new_stomp_params
        else:
            old_stomp = conn_params.pop("stomp", None)

            if old_stomp is not None:
                messages.append(
                    "Removed unparseable stomp connnection params from garden "
                    f"{garden_name}"
                )
    else:  # must be STOMP
        if "stomp" not in conn_params or new_stomp_params == {}:
            # if you tell us the type is STOMP, but don't provide stomp conn params,
            # we'll force it to be HTTP rather than fail
            messages.append(f"Forcing connection type to HTTP for garden {garden_name}")
            garden.connection_type = "HTTP"

            new_http_params, http_msgs = _clean_or_default_http_connection_params(
                conn_params.get("http", None), garden_name
            )
            conn_params["http"] = new_http_params

            if "stomp" in conn_params:
                _ = conn_params.pop("stomp")
        else:
            conn_params["stomp"] = new_stomp_params

            new_http_params, http_msgs = _clean_or_empty_http_connection_params(
                conn_params.get("http", None), garden_name
            )

            if "http" in conn_params and new_http_params == {}:
                messages.append(
                    "Removed unparseable http configuration params from "
                    f"garden {garden_name}"
                )
                _ = conn_params.pop("http")
            elif new_http_params != {}:
                conn_params["http"] = new_http_params

    garden.connection_params = conn_params

    for msg in messages + http_msgs + stomp_msgs:
        logger.debug(msg)

    return garden


@publish_event(BrewtilsEvents.GARDEN_CREATED)
def create_garden(garden: BrewtilsGarden) -> BrewtilsGarden:
    """Create a new Garden

    Args:
        garden: The Garden to create

    Returns:
        The created Garden

    """
    garden = clean_garden_connection_params(garden)
    garden.status_info["heartbeat"] = datetime.utcnow()

    return db.create(garden)


def garden_add_system(system: BrewtilsSystem, garden_name: str) -> BrewtilsGarden:
    """Add a System to a Garden

    Args:
        system: The system to add
        garden_name: The Garden Name to add it to

    Returns:
        The updated Garden

    """
    try:
        garden = get_garden(garden_name)
    except DoesNotExist:
        raise PluginError(
            f"Garden '{garden_name}' does not exist, unable to map '{str(system)}"
        )

    if system.namespace not in garden.namespaces:
        garden.namespaces.append(system.namespace)

    if str(system) not in garden.systems:
        garden.systems.append(str(system))

    return update_garden(garden)


@publish_event(BrewtilsEvents.GARDEN_UPDATED)
def update_garden(garden: BrewtilsGarden) -> BrewtilsGarden:
    """Update a Garden

    Args:
        garden: The Garden to update

    Returns:
        The updated Garden
    """

    return db.update(clean_garden_connection_params(garden))


def garden_sync(sync_target: str = None):
    """Do a garden sync

    If we're here it means the Operation.target_garden_name was *this* garden. So the
    sync_target is either *this garden* or None.

    If the former then call the method to publish the current garden.

    If the latter then we need to send sync operations to *all* known downstream
    gardens.

    Args:
        sync_target:

    Returns:

    """
    # If a Garden Name is provided, determine where to route the request
    if sync_target:
        logger.debug("Processing garden sync, about to publish")

        publish_garden()

    else:
        from beer_garden.router import route

        # Iterate over all gardens and forward the sync requests
        for garden in get_gardens(include_local=False):
            logger.debug(f"About to create sync operation for garden {garden.name}")

            route(
                BrewtilsOperation(
                    operation_type="GARDEN_SYNC",
                    target_garden_name=garden.name,
                    kwargs={"sync_target": garden.name},
                )
            )


def handle_event(event):
    """Handle garden-related events

    For GARDEN events we only care about events originating from downstream. We also
    only care about immediate children, not grandchildren.

    Whenever a garden event is detected we should update that garden's database
    representation.

    This method should NOT update the routing module. Let its handler worry about that!
    """
    if event.garden != config.get("garden.name"):

        if event.name in (
            BrewtilsEvents.GARDEN_STARTED.name,
            BrewtilsEvents.GARDEN_UPDATED.name,
            BrewtilsEvents.GARDEN_STOPPED.name,
            BrewtilsEvents.GARDEN_SYNC.name,
        ):
            # Only do stuff for direct children
            if event.payload.name == event.garden:
                try:
                    existing_garden = get_garden(event.payload.name)
                except DoesNotExist:
                    existing_garden = None

                for system in event.payload.systems:
                    system.local = False

                if existing_garden is None:
                    event.payload.connection_type = None
                    event.payload.connection_params = {}

                    garden = create_garden(event.payload)
                else:
                    for attr in ("status", "status_info", "namespaces", "systems"):
                        setattr(existing_garden, attr, getattr(event.payload, attr))

                    garden = update_garden(existing_garden)

                # Publish update events for UI to dynamically load changes for Systems
                for system in garden.systems:
                    publish(
                        BrewtilsEvent(
                            name=BrewtilsEvents.SYSTEM_UPDATED.name,
                            garden=event.garden,
                            payload_type="System",
                            payload=system,
                        )
                    )

    elif event.name == BrewtilsEvents.GARDEN_UNREACHABLE.name:
        target_garden = get_garden(event.payload.target_garden_name)

        if target_garden.status not in [
            "UNREACHABLE",
            "STOPPED",
            "BLOCKED",
            "ERROR",
        ]:
            update_garden_status(event.payload.target_garden_name, "UNREACHABLE")
    elif event.name == BrewtilsEvents.GARDEN_ERROR.name:
        target_garden = get_garden(event.payload.target_garden_name)

        if target_garden.status not in [
            "UNREACHABLE",
            "STOPPED",
            "BLOCKED",
            "ERROR",
        ]:
            update_garden_status(event.payload.target_garden_name, "ERROR")
    elif event.name == BrewtilsEvents.GARDEN_NOT_CONFIGURED.name:
        target_garden = get_garden(event.payload.target_garden_name)

        if target_garden.status == "NOT_CONFIGURED":
            update_garden_status(event.payload.target_garden_name, "NOT_CONFIGURED")
