import configparser
import logging
import shlex

from ytdl_qt.paths import Paths


class Config:

	def __init__(self, path=None):
		self.core = None

		self.ffmpeg_path = None
		self.player_path = None
		self.player_params = []

		self.read(path)

	def read(self, path=None):
		if not path:
			path = Paths.get_config_path()
		self.core = configparser.ConfigParser()
		self.core.read(path)

		try:
			self.ffmpeg_path = self.core['Paths'].get('ffmpeg_path', None)
			self.player_path = self.core['Paths'].get('player_path', None)

			player_params_str = self.core['Paths'].get('player_params', '')
			self.player_params = shlex.split(player_params_str)
		except KeyError:
			pass

	def save(self, path=None):
		assert self.core
		if not path:
			path = Paths.get_config_path()

		self.core['Paths'] = {
			'ffmpeg_path': '' if not self.ffmpeg_path else self.ffmpeg_path,
			'player_path': '' if not self.player_path else self.player_path,
			'player_params': shlex.join(self.player_params)
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

