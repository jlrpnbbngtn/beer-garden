from typing import List

import pytest
from brewtils.models import Command as BrewtilsCommand
from brewtils.models import Garden as BrewtilsGarden
from brewtils.models import Instance as BrewtilsInstance
from brewtils.models import System as BrewtilsSystem
from mongoengine import connect

from beer_garden.db.mongo.api import to_brewtils
from beer_garden.db.mongo.models import Garden, System

SYSTEMS = "systems"
GARDEN_NAMESPACE = "namespace1"


class TestGardenSchema:
    @classmethod
    def setup_class(cls):
        connect("beer_garden", host="mongomock://localhost")
        Garden.drop_collection()
        Garden.ensure_indexes()
        System.drop_collection()
        System.ensure_indexes()

    @pytest.fixture
    def systems(self) -> List[System]:
        system_count = 3
        the_systems = []

        for index in range(system_count):
            instance = {}
            command = dict(name=f"mycommand{index}", parameters=[])

            the_systems.append(
                System(
                    name=f"system{index}",
                    description=f"System {index}",
                    version="0.0.1",
                    namespace=GARDEN_NAMESPACE,
                    max_instances=1,
                    icon_name="myicon",
                    display_name=f"My Awesome System {index}",
                    metadata={"something": "important"},
                    local=True,
                    template="mytemplate",
                    instances=[instance],
                    commands=[command],
                ).save()
            )
        return the_systems

    @pytest.fixture
    def full_garden(self, systems) -> BrewtilsGarden:
        the_garden = Garden(
            name="childgarden",
            status="RUNNING",
            connection_type="HTTP",
            connection_params={
                "http": {"host": "gardenhost", "port": 2337, "url_prefix": "/"}
            },
            namespaces=[GARDEN_NAMESPACE],
        ).save()

        the_garden.systems = [system.to_dbref() for system in systems]
        garden = the_garden.save()

        yield garden

        for system in systems:
            system.delete()

        garden.delete()

    def test_to_brewtils_dumps_garden_systems_to_brewtils_models(self, full_garden):
        brewtils_garden = to_brewtils(full_garden)
        brewtils_systems_list = getattr(brewtils_garden, SYSTEMS)

        for brewtils_system in brewtils_systems_list:
            assert type(brewtils_system) == BrewtilsSystem

            # no need to go lower than the top level children; if it got that right,
            #  it's safe to assume it got the children of the children right too
            for brewtils_instance in brewtils_system.instances:
                assert type(brewtils_instance) == BrewtilsInstance
            for brewtils_command in brewtils_system.commands:
                assert type(brewtils_command) == BrewtilsCommand
