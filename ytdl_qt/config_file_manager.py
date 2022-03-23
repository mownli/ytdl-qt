import configparser
import logging

from ytdl_qt.paths import Paths


class ConfigFileManager:

    def __init__(self, path=None):
        self.core = None

        self.ffmpeg_path: str = ''
        self.player_path: str = ''
        self.player_params: str = ''
        self.download_dir: str = ''

        self.read(path)

    def read(self, path=None):
        if not path:
            path = Paths.get_config_path()
        self.core = configparser.ConfigParser()
        self.core.read(path)

        try:
            self.ffmpeg_path = self.core['Paths'].get('ffmpeg_path', '')
            self.player_path = self.core['Paths'].get('player_path', '')
            self.download_dir = self.core['Paths'].get('download_dir', '')

            self.player_params = self.core['Paths'].get('player_params', '')
        except KeyError:
            pass

    def save(self, path=None):
        assert self.core
        if not path:
            path = Paths.get_config_path()

        self.core['Paths'] = {
            'ffmpeg_path': '' if not self.ffmpeg_path else self.ffmpeg_path,
            'player_path': '' if not self.player_path else self.player_path,
            'player_params': '' if not self.player_params else self.player_params,
            'download_dir': '' if not self.download_dir else self.download_dir,
        }

        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as configfile:
            self.core.write(configfile)
            logging.debug(f'Created config file at {path}')

# def __getitem__(self, item):
# 	assert self.core
# 	return self.core[item]
#
# def __setitem__(self, key, value):
# 	assert self.core
# 	self.core[key] = value
