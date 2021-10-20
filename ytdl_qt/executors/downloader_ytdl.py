#!/usr/bin/env python3

import datetime
import logging
import threading
from math import floor
import copy

from yt_dlp import YoutubeDL
#from youtube_dl import YoutubeDL

from ytdl_qt.downloader_abstract import DownloaderAbstract
from ytdl_qt import utils
from ytdl_qt.ytdl_info import Info


class DownloaderYtdl(DownloaderAbstract):

	class Cancelled(Exception):
		pass

	def __init__(self, params, ytdl_info):
		super().__init__(copy.copy(params), ytdl_info)

		self._download_ct: int = len(params.fmt_id_selection)
		self._cancel_flag: bool = False

		self.params.ytdl_params = self.params.ytdl_params.copy()
		self.params.ytdl_params.update({
			Info.Keys.format_requested: self.ytdl_info.get_format_str(params.fmt_id_selection),
			Info.Keys.hooks: [self.ytdl_processing_hook],
		})

	def _setup_ui(self):
		self.set_progress_max_cb(100)
		self.send_msg_cb('Downloading target')

	def _do(self):
		try:
			with YoutubeDL(self.params.ytdl_params) as ytdl:
				ytdl.download([self.ytdl_info.get_url()])
		except self.Cancelled:
			self.send_msg_cb('Cancelled')
			self.finished_cb(self)
		except Exception as e:
			self.send_msg_cb('Download Error')
			self.error = str(e)
			self.finished_cb(self)

	def download_start(self):
		self._setup_ui()
		#self._download_ct = self.ytdl.get_number_of_files_to_download()

		self._monitor = threading.Thread(target=self._do, daemon=True)
		self._monitor.start()

	def download_cancel(self):
		self._cancel_flag = True

	def ytdl_processing_hook(self, d: dict):
		"""
		YoutubeDl hook that sometimes gets called during download.
		Does callbacks to UI. Throws exception on error.
		"""
		logging.debug('Entered hook')
		if self._cancel_flag:
			raise self.Cancelled
		self.update_ui_cb()
		# Status dictionary
		if d[Info.Keys.status] == Info.Keys.downloading:
			total_str = ''
			downloaded = d[Info.Keys.downloaded_bytes]
			downloaded_str = utils.convert_size(downloaded)
			if Info.Keys.total_bytes in d:
				total = d[Info.Keys.total_bytes]
				self.set_progress_val_cb(floor(downloaded / total * 100))
				total_str = utils.convert_size(total)
			elif Info.Keys.total_bytes_estimate in d:
				total = d[Info.Keys.total_bytes_estimate]
				self.set_progress_val_cb(floor(downloaded / total * 100))
				total_str = utils.convert_size(total)

			msg = ''
			if utils.check_dict_attribute(d, Info.Keys.eta):
				msg += f"ETA: {str(datetime.timedelta(seconds=d[Info.Keys.eta]))}    "
			msg += f"{downloaded_str} / {total_str}"
			self.send_msg_cb(msg)

		elif d[Info.Keys.status] == Info.Keys.finished:
			logging.debug('Hook status = finished')
			self._download_ct -=  1
			if self._download_ct == 0:
				self.file_ready_for_playback_cb(d[Info.Keys.filename])
				self.send_msg_cb('Download Finished')
				self.finished_cb(self)

		elif d[Info.Keys.status] == Info.Keys.error:
			raise Exception('Something happened inside youtube-dl')
