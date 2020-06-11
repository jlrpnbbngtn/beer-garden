# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from typing import List

from brewtils.errors import PluginError
from brewtils.models import Events, Garden, System

import beer_garden.config as config
import beer_garden.db.api as db
from beer_garden.events import publish_event
from beer_garden.systems import get_systems

logger = logging.getLogger(__name__)


def get_garden(garden_name: str) -> Garden:
    """Retrieve an individual Garden

    Args:
        garden_name: The name of Garden

    Returns:
        The Garden

    """
    if garden_name == config.get("garden.name"):
        return get_local_garden()
    return db.query_unique(Garden, name=garden_name)


def get_gardens() -> List[Garden]:
    """Retrieve list of all Gardens

    Returns:
        The Garden list

    """

    query_results = db.query(Garden)
    if query_results:
        query_results.append(get_local_garden())
        return query_results
    return [get_local_garden()]


def get_local_garden() -> Garden:
    """Retrieved the local garden object

    Returns:
        Garden Object

    """
    local_garden = Garden(
        name=config.get("garden.name"),
        connection_type="LOCAL",
        systems=get_systems(filter_params={"local": True}),
        status="RUNNING",
        status_info="This is your local Garden record, not persisted in the Database. "
        "Changes will not be reflected",
    )
    for system in local_garden.systems:
        if system.namespace not in local_garden.namespaces:
            local_garden.namespaces.append(system.namespace)

    return local_garden


def update_garden_config(garden: Garden):
    db_garden = db.query_unique(Garden, id=garden.id)
    db_garden.connection_params = garden.connection_params
    db_garden.connection_type = garden.connection_type

    return update_garden(db_garden)


def update_garden_status(garden_name: str, new_status: str) -> Garden:
    """Update an Garden status.

    Will also update the status_info heartbeat.

    Args:
        garden_name: The Garden Name
        new_status: The new status

    Returns:
        The updated Garden
    """
    garden = db.query_unique(Garden, name=garden_name)
    garden.status = new_status
    garden.status_info["heartbeat"] = datetime.utcnow()

    return update_garden(garden)


@publish_event(Events.GARDEN_REMOVED)
def remove_garden(garden_name: str) -> None:
    """Remove a garden

        Args:
            garden_name: The Garden name

        Returns:
            None

        """
    garden = db.query_unique(Garden, name=garden_name)
    db.delete(garden)
    return garden


@publish_event(Events.GARDEN_CREATED)
def create_garden(garden: Garden) -> Garden:
    """Create a new Garden

    Args:
        garden: The Garden to create

    Returns:
        The created Garden

    """
    garden.status = "INITIALIZING"
    garden.status_info["heartbeat"] = datetime.utcnow()

    return db.create(garden)


def garden_add_system(system: System, garden_name: str):
    garden = get_garden(garden_name)

    if garden is None:
        raise PluginError(
            f"Garden '{garden_name}' does not exist, unable to map '{str(system)}"
        )

    if system.namespace not in garden.namespaces:
        garden.namespaces.append(system.namespace)

    if str(system) not in garden.systems:
        garden.systems.append(str(system))

    return update_garden(garden)


@publish_event(Events.GARDEN_UPDATED)
def update_garden(garden: Garden):
    return db.update(garden)


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
            Events.GARDEN_STARTED.name,
            Events.GARDEN_UPDATED.name,
            Events.GARDEN_STOPPED.name,
        ):
            # Only do stuff for direct children
            if event.payload.name == event.garden:
                existing_garden = get_garden(event.payload.name)

                if existing_garden is None:
                    create_garden(event.payload)
                else:
                    for attr in ("status", "status_info", "namespaces", "systems"):
                        setattr(existing_garden, attr, getattr(event.payload, attr))

                    update_garden(existing_garden)
