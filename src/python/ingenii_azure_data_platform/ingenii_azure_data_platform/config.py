from os import getenv

import hiyapyco as hco
import yamale


class CloudRegionException(Exception):
    ...


class CloudRegion:
    """
    A class that has all Azure region names and their respective short names.
    """

    _regions = {
        "EastUS": "eus",
        "EastUS2": "eus2",
        "CentralUS": "cus",
        "NorthCentralUS": "ncus",
        "SouthCentralUS": "scus",
        "WestCentralUS": "wcus",
        "WestUS": "wus",
        "WestUS2": "wus2",
        "WestUS3": "wus3",
        "AustraliaEast": "aue",
        "AustraliaCentral": "auc",
        "AustraliaCentral2": "auc2",
        "AustraliaSouthEast": "ause",
        "SouthAfricaNorth": "san",
        "SouthAfricaWest": "saw",
        "CentralIndia": "cin",
        "SouthIndia": "sin",
        "WestIndia": "win",
        "EastAsia": "eas",
        "SouthEastAsia": "seas",
        "JapanEast": "jpe",
        "JapanWest": "jpw",
        "JioIndiaWest": "jinw",
        "JioIndiaCentral": "jinc",
        "KoreaCentral": "koc",
        "KoreaSouth": "kos",
        "CanadaCentral": "cac",
        "CanadaEast": "cae",
        "FranceCentral": "frc",
        "FranceSouth": "frs",
        "GermanyWestCentral": "gewc",
        "GermanyNorth": "gen",
        "NorwayEast": "nwye",
        "NorwayWest": "nwyw",
        "SwitzerlandNorth": "swn",
        "SwitzerlandWest": "sww",
        "UAENorth": "uaen",
        "UAECentral": "uaec",
        "BrazilSouth": "brs",
        "BrazilSouthEast": "brse",
        "NorthEurope": "neu",
        "WestEurope": "weu",
        "SwedenCentral": "swec",
        "SwedenSouth": "swes",
        "UKSouth": "uks",
        "UKWest": "ukw",
    }

    _regions_lowercase_keys = {k.lower(): v for k, v in _regions.items()}

    def __init__(self, name: str) -> None:
        self._name = name.lower()

        if self._name not in self._regions_lowercase_keys:
            raise CloudRegionException(f"Region with name'{self._name}' not found!")

    @property
    def short_name(self):
        return self._regions_lowercase_keys[self._name]

    @property
    def long_name(self):
        for k, _ in self._regions.items():
            if k.lower() == self._name:
                return k


class PlatformConfigurationException(Exception):
    ...


class PlatformConfiguration:
    """
    Platform configuration class that handles config reading and schema validation.
    Each Pulumi project needs a single instance of this class. The instance can be passed around to
    other objects that expect it.

    Properties
    ----------

    The class exposes the following properties:

    * stack         - the current Pulumi stack name
    * prefix        - the resource prefix (extracted from the YML configs)
    * region        - the Azure region (extracted from the YML configs)
    * tags          - the global tags (extracted from the YML configs)
    * unique_id     - the unique string id (extracted from the YML configs)
    * yml_config    - the yml config dictionary
    """

    def _validate_schema(self, schema_file_path: str, yml_config: dict):
        schema = yamale.make_schema(schema_file_path)
        data = yamale.make_data(content=hco.dump(yml_config))
        try:
            yamale.validate(schema, data)
            print("The configuration schema is valid. ✅")
        except ValueError as e:
            print(f"The configuration schema is NOT valid! ❌\n{e}")
            exit(1)

    def __init__(
        self,
        stack: str,
        config_schema_file_path: str,
        default_config_file_path: str,
        custom_config_file_path: str = None,
    ) -> None:

        # If no custom config file path is provided, we'll use the default config.
        custom_config_file_path = custom_config_file_path or default_config_file_path

        # Merge the default + custom configs. The custom configs will override any defaults.
        self._from_yml = dict(
            hco.load(
                [default_config_file_path, custom_config_file_path],
                method=hco.METHOD_MERGE,
                mergelists=False,
            )
        )  # type: ignore

        # Validate the schema
        self._validate_schema(config_schema_file_path, self._from_yml)

        # Add properties
        self._prefix = self._from_yml["general"]["prefix"]
        self._region = CloudRegion(self._from_yml["general"]["region"])
        self._tags = self._from_yml["general"]["tags"]
        self._unique_id = self._from_yml["general"]["unique_id"]
        self._use_legacy_naming = self._from_yml["general"]["use_legacy_naming"]
        
        # Returns 'True' if the resource protection is enabled, 'False' otherwise.
        self._resource_protection = bool(int(getenv("ENABLE_RESOURCE_PROTECTION", 1)))

        self._stack = stack.lower()

        # In the new naming convention, we have shortened the stack names if they are either test, prod or shared.
        self._stack_short_name = {"test": "tst", "prod": "prd", "shared": "shr"}.get(
            self._stack, self._stack
        )

    @property
    def from_yml(self):
        return self._from_yml

    @property
    def prefix(self):
        return self._prefix

    @property
    def region(self):
        return self._region

    @property
    def stack(self):
        return self._stack

    @property
    def stack_short_name(self):

        # If we use the legacy naming conventions, we pass the long name
        if self._use_legacy_naming:
            return self._stack
        else:
            return self._stack_short_name

    @property
    def tags(self):
        return self._tags

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def resource_protection(self):
        return self._resource_protection

    @property
    def use_legacy_naming(self):
        return self._use_legacy_naming

    # TODO: Left for backward compatibility. To be deleted in future releases.
    @property
    def yml_config(self):
        return self.from_yml

    def __getitem__(self, key):
        return self.from_yml[key]

    def __setitem__(self, key, value):
        raise Exception("You should not be updating the platform configuration!")
