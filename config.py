import os, json, base64, uuid

class Config:
	DEFAULT_CONFIG = {
        "browser": "firefox",
        "delay": 0.25,
		"fallback_extension": "png",
		"comics": [{
			"name": "Comic Name",
			"url": "COMIC_PAGE_1_URL",
			"page_num": 1,
			"image_selector": ["id", "cc-comic"],
			"title_selector": ["class_name", "cc-newsheader"],
			"next_selector": ["class_name", "cc-next"]
		}]
	}

	def __init__(self, fileName):
		self._fileName = fileName
		self._store = self._readConfig()
		self._ensureDefaultsExist()

	def _ensureDefaultsExist(self, config=None, default=None):
		# If config and default are None, start with the initial configuration
		if config is None:
			config = self._store
		if default is None:
			default = self.DEFAULT_CONFIG

		# Flag to track if changes were made
		writeConfig = False

		# Iterate over the keys in the default configuration
		for key, value in default.items():
		# If the key is not in the configuration, add it with its default value
			if key not in config:
				config[key] = value
				writeConfig = True
			# If the value is a dictionary, recursively call _ensureDefaultsExist for nested keys
			elif isinstance(value, dict) and isinstance(config[key], dict):
				wasChanged = self._ensureDefaultsExist(config[key], value)
				if wasChanged:
					writeConfig = True

		# Write the updated configuration to file if changes were made
		if writeConfig and config is self._store:
			self._writeConfig()

		return writeConfig

	def _writeConfig(self):
		try:
			# Open the file in write mode, creating it if it doesn't exist
			with open(self._fileName, mode="w") as file:
				# Serialize the configuration dictionary to JSON and write it to the file
				json.dump(self._store, file, indent=4)
		except FileNotFoundError as e:
			# Raise an error if the specified file path does not exist or is inaccessible
			raise FileNotFoundError(f"Could not write configuration: {e}")
		except IOError as e:
			# Raise an error if an I/O error occurs while writing to the file
			raise IOError(f"An I/O error occurred while writing configuration: {e}")

	def _readConfig(self):
		try:
			# Open the file in read mode
			with open(self._fileName, mode="r") as file:
				# Deserialize the JSON data from the file into a dictionary
				return json.load(file)
		except FileNotFoundError as e:
			# Raise an error if the specified file path does not exist or is inaccessible
			raise FileNotFoundError(f"Could not read configuration: {e}")
		except IOError as e:
			# Raise an error if an I/O error occurs while reading from the file
			raise IOError(f"An I/O error occurred while reading configuration: {e}")
		except json.JSONDecodeError as e:
			# Raise an error if the file is not in valid JSON format
			raise json.JSONDecodeError(f"Invalid JSON format: {e.msg}", e.doc, e.pos)

	def get(self, key: str):
		return self._store.get(key)

	def set(self, key: str, value: str):
		self._store.update({key: value})

	def pop(self, key: str):
		self._store.pop(key)
