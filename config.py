from typing import Any
import os
import json
import copy

class Config:
    DEFAULT_CONFIG = {
        "browser": "firefox",
        "delay": 0.25,
        "fallback_extension": "png",
        "download_by": "order", # order, name_desc, name_asc
        "overwrite_existing": False,
        "update_config": False, # this will re-order if download_by is anything other than 'order'
        "comics": [{
            "enabled": True,
            "name": "Comic Name",
            "url": "COMIC_PAGE_1_URL",
            "page_num": 1,
            "image_selector": ["id", "cc-comic"],
            "title_selector": ["class_name", "cc-newsheader"],
            "next_selector": ["class_name", "cc-next"]
        }]
    }

    def __init__(self, fileName: str) -> None:
        self._fileName = fileName
        self._store = self._readConfig()
        self._ensureDefaultsExist()
        # Validate certain config values
        allowed_download_by = {"order", "name_desc", "name_asc"}
        current_download_by = self._store.get("download_by")
        if current_download_by not in allowed_download_by:
            print(f"Warning: Invalid download_by '{current_download_by}'. Falling back to 'order'.")
            self._store["download_by"] = "order"
            self._writeConfig()

    def _ensureDefaultsExist(self, config: dict | None = None, default: dict | None = None) -> bool:
        # If config and default are None, start with the initial configuration
        if config is None:
            config = self._store
        if default is None:
            default = self.DEFAULT_CONFIG

        writeConfig = False

        for key, value in default.items():
            if key not in config:
                # Insert a deep copy to avoid mutating DEFAULT_CONFIG
                config[key] = copy.deepcopy(value)
                writeConfig = True
            elif isinstance(value, dict) and isinstance(config[key], dict):
                if self._ensureDefaultsExist(config[key], value):
                    writeConfig = True
            elif isinstance(value, list) and isinstance(config[key], list):
                # If default is a list of dicts, patch defaults into each dict item
                if value and isinstance(value[0], dict):
                    item_default = value[0]
                    for item in config[key]:
                        if isinstance(item, dict):
                            if self._ensureDefaultsExist(item, item_default):
                                writeConfig = True

        if writeConfig and config is self._store:
            self._writeConfig()

        return writeConfig

    def _writeConfig(self) -> None:
        try:
            directory = os.path.dirname(self._fileName)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(self._fileName, mode="w") as file:
                json.dump(self._store, file, indent=4)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Could not write configuration: {e}")
        except IOError as e:
            raise IOError(f"An I/O error occurred while writing configuration: {e}")

    def _readConfig(self) -> dict:
        try:
            with open(self._fileName, mode="r") as file:
                return json.load(file)
        except FileNotFoundError:
            # First run: create from defaults and persist
            store = copy.deepcopy(self.DEFAULT_CONFIG)
            self._store = store
            self._writeConfig()
            return store
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {self._fileName}: {e}") from e
        except IOError as e:
            raise IOError(f"An I/O error occurred while reading configuration: {e}")

    def get(self, key: str) -> Any:
        return self._store.get(key)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def save(self) -> None:
        self._writeConfig()

    def pop(self, key: str, default: Any | None = None) -> Any:
        return self._store.pop(key, default)
