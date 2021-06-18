#!/usr/bin/env python3

import datetime
import logging
import threading
from math import floor

from ytdl_qt.downloader_abstract import DownloaderAbstract
from ytdl_qt import utils


class DownloaderYtdl(DownloaderAbstract):

	class Cancelled(Exception):
		pass

	def __init__(self, ytdl):
		super().__init__(ytdl)
		self.ytdl.add_progress_hook(self.ytdl_processing_hook)
		self._download_ct: int = 0
		self._cancel_flag: bool = False

	def _setup_ui(self):
		self.set_progress_max_cb(100)
		self.send_msg_cb('Downloading target')

	def _do(self):
		try:
			self.ytdl.download([self.ytdl.get_current_url()])
		except self.Cancelled:
			self.send_msg_cb('Cancelled')
			self.finished_cb(self)
		except Exception as e:
			self.send_msg_cb('Download Error')
			self.error = str(e)
			self.finished_cb(self)
		finally:
			# Needed after every ytdl download to avoid future format collisions
			self.ytdl.reset_format()
			self.ytdl.set_progress_hooks([])

	def download_start(self):
		self._setup_ui()
		self._download_ct = self.ytdl.get_number_of_files_to_download()

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
		# self.update_ui_cb()
		# Status dictionary
		if d[self.ytdl.Keys.status] == self.ytdl.Keys.downloading:
			total_str = ''
			downloaded = d[self.ytdl.Keys.downloaded_bytes]
			downloaded_str = utils.convert_size(downloaded)
			if self.ytdl.Keys.total_bytes in d:
				total = d[self.ytdl.Keys.total_bytes]
				self.set_progress_val_cb(floor(downloaded / total * 100))
				total_str = utils.convert_size(total)
			elif self.ytdl.Keys.total_bytes_estimate in d:
				total = d[self.ytdl.Keys.total_bytes_estimate]
				self.set_progress_val_cb(floor(downloaded / total * 100))
				total_str = utils.convert_size(total)

			msg = ''
			if utils.check_dict_attribute(d, self.ytdl.Keys.eta):
				msg += f"ETA: {str(datetime.timedelta(seconds=d[self.ytdl.Keys.eta]))}    "
			msg += f"{downloaded_str} / {total_str}"
			self.send_msg_cb(msg)

		elif d[self.ytdl.Keys.status] == self.ytdl.Keys.finished:
			logging.debug('Hook status = finished')
			self._download_ct = self._download_ct - 1
			if self._download_ct == 0:
				self.file_ready_for_playback_cb(d[self.ytdl.Keys.filename])
				self.send_msg_cb('Download Finished')
				self.finished_cb(self)

		elif d[self.ytdl.Keys.status] == self.ytdl.Keys.error:
			raise Exception('Something happened inside youtube-dl')
