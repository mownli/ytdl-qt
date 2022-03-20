import os

from ytdl_qt.config_file_manager import ConfigFileManager
from ytdl_qt.paths import Paths


class Setting:

	def __init__(self, default=''):
		self.default: str = default
		self.current: str = ''

	def set(self, arg: str):
		# self.changed = True
		# self.previous = self.current
		if not arg:
			self.current = self.default
		else:
			self.current = arg


class FfmpegSetting(Setting):

	def __init__(self, default):
		super().__init__(default)

	def set(self, arg: str):
		if arg:
			# ffmpeg_path = PurePath(arg)
			# if ffmpeg_path.name != PurePath('ffmpeg').name and ffmpeg_path.name != PurePath('ffmpeg.exe').name:
			# 	raise Exception('Inappropriate name of the FFmpeg executable')
			# else:
			# 	super().set(arg)

			ffmpeg_filename = os.path.basename(arg)
			if ffmpeg_filename != 'ffmpeg' and ffmpeg_filename != 'ffmpeg.exe':
				raise Exception('Inappropriate name of the FFmpeg executable')
			else:
				super().set(arg)
		else:
			super().set('')

# class DownloadDirSetting(Setting):
#
# 	def __init__(self, default=''):
# 		super().__init__(default)
#
# 	def set(self, arg: str):
# 		"""Adds trailing slash."""
# 		super().set(os.path.abspath(arg))


class Settings:

	def __init__(self):
		self.ffmpeg_path = FfmpegSetting(Paths.get_ffmpeg_path())
		self.player_path = Setting()
		self.player_params = Setting()
		#self.download_dir = DownloadDirSetting()
		self.download_dir = Setting()

		self.config = ConfigFileManager()

		self.ffmpeg_path.set(self.config.ffmpeg_path)
		self.player_path.set(self.config.player_path)
		self.player_params.set(self.config.player_params)
		self.download_dir.set(self.config.download_dir)

	def save(self):
		self.config.ffmpeg_path = self.ffmpeg_path.current
		self.config.player_path = self.player_path.current
		self.config.player_params = self.player_params.current
		self.config.download_dir = self.download_dir.current
		self.config.save()
