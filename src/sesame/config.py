import os

from simple_toml_configurator import Configuration

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "sesame.db")


class Config(Configuration):
    # added this to show which configurable values can be changed by the user
    configurable_keys = {
        "db_path": {
            "attribute": "vault_db_path",
            "description": "Filesystem path to the vault (SQLite) database file",
        },
    }

    def __init__(self, config_path: str = CONFIG_DIR):
        default_config = {
            "vault": {
                "db_path": DEFAULT_DB_PATH,
            },
            "app": {
                "setup_complete": False,
            },
        }
        super().__init__(config_path, default_config, config_file_name="config")

    @property
    def is_first_run(self) -> bool:
        return not self.app_setup_complete

    def mark_setup_complete(self) -> None:
        self.update_config({"app_setup_complete": True})

    def get_configurable_value(self, name: str):
        if name not in self.configurable_keys:
            raise ValueError(f"'{name}' is not a configurable setting.")
        return getattr(self, self.configurable_keys[name]["attribute"])

    def set_configurable_value(self, name: str, value) -> None:
        if name not in self.configurable_keys:
            raise ValueError(f"'{name}' is not a configurable setting.")
        attribute = self.configurable_keys[name]["attribute"]
        self.update_config({attribute: value})
