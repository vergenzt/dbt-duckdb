from typing import Any
from typing import Dict

from duckdb import DuckDBPyConnection

from . import BasePlugin
from dbt.adapters.duckdb.__version__ import version as __plugin_version__
from dbt.adapters.duckdb.credentials import DuckDBCredentials
from dbt.version import __version__


class Plugin(BasePlugin):
    def initialize(self, config: Dict[str, Any]):
        self._token = config.get("token")

    def configure_connection(self, conn: DuckDBPyConnection):
        conn.load_extension("motherduck")
        # If a MotherDuck database is attached after the database
        # instance is created, set the motherduck token
        if self.creds is not None:
            if self.creds.is_motherduck_attach:
                if self._token:
                    conn.execute(f"SET motherduck_token = '{self._token}'")
                elif self.creds.settings:
                    if "motherduck_token" in self.creds.settings:
                        token = self.creds.settings.pop("motherduck_token")
                        conn.execute(f"SET motherduck_token = '{token}'")

    @staticmethod
    def token_from_config(creds: DuckDBCredentials) -> str:
        """Load the token from the MotherDuck plugin config
        If not specified, this returns an empty string

        :param str: MotherDuck token
        """
        plugins = creds.plugins or []
        for plugin in plugins:
            if plugin.config:
                if "token" in plugin.config or "motherduck_token" in plugin.config:
                    token = plugin.config.get("token") or plugin.config.get("motherduck_token")
                    return str(token)
        return ""

    def update_connection_config(self, creds: DuckDBCredentials, config: Dict[str, Any]):
        user_agent = f"dbt/{__version__} dbt-duckdb/{__plugin_version__}"
        if "custom_user_agent" in config:
            user_agent = f"{user_agent} {config['custom_user_agent']}"
        settings: Dict[str, Any] = creds.settings or {}
        if "custom_user_agent" in settings:
            user_agent = f"{user_agent} {settings.pop('custom_user_agent')}"

        config["custom_user_agent"] = user_agent

        # If a user specified the token via the plugin config,
        # pass it to the config kwarg in duckdb.connect
        if not creds.is_motherduck_attach:
            token = self.token_from_config(creds)
            if token != "":
                config["motherduck_token"] = token
