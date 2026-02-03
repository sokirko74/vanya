
import json
import os


class TConfig:
    def __init__(self):
        self._path =  os.path.join(
            os.path.dirname(__file__), "settings.json")

        self.saved_urls = dict()
        self.simple_queries = set()
        self._config = dict()
        self._read()


    def _read(self):
        with open(self._path) as inp:
            self._config = json.load(inp)
        self.simple_queries.clear()
        for k, cat  in self._config['SIMPLE_QUERIES'].items():
            self.simple_queries.update(cat)
        self.saved_urls = self._config['URLS']

    def _write(self):
        with open(self._path, "w") as outp:
            json.dump(self._config, outp)

    def save_channel_alias(self, real_channel_name, alias):
        if 'channel_aliases' not in self._config:
            self._config['channel_aliases'] = dict()
        self._config['channel_aliases'][alias] = real_channel_name

    def translate_alias(self, alias):
        return self._config.get('channel_aliases', {}).get(alias)
