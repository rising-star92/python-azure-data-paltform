import yamale
import hiyapyco as hco
from hashlib import md5


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
        if custom_config_file_path is None:
            custom_config_file_path = default_config_file_path

        # Merge the default + custom configs. The custom configs will override any defaults.
        self._yml_config = dict(
            hco.load(
                [default_config_file_path, custom_config_file_path],
                method=hco.METHOD_MERGE,
                mergelists=False,
            )
        )  # type: ignore

        # Validate the schema
        self._validate_schema(config_schema_file_path, self._yml_config)

        self._stack = stack

    @property
    def stack(self):
        return self._stack

    @property
    def prefix(self):
        return self._yml_config["general"]["prefix"]

    @property
    def region(self):
        return CloudRegion(self._yml_config["general"]["region"])

    @property
    def tags(self):
        return self._yml_config["general"]["tags"]

    @property
    def unique_id(self):
        return self._yml_config["general"]["unique_id"]

    @property
    def yml_config(self):
        return self._yml_config
