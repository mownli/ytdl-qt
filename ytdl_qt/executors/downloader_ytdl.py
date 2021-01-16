#!/usr/bin/env python3

import datetime
import logging
from math import floor

from PyQt5.QtWidgets import (
	QApplication,
)

from ytdl_qt.downloader_abstract import DownloaderAbstract
from ytdl_qt import utils


class DownloaderYtdl(DownloaderAbstract):

	class Cancelled(Exception):
		pass

	def __init__(self, ytdl):
		logging.debug('Instantiating DownloaderYtdl')
		super().__init__(ytdl)
		self._ytdl.add_progress_hook(self.ytdl_processing_hook)
		self._download_ct: int = 0
		self._cancel_flag: bool = False

	def _setup_ui(self):
		self.set_pbar_max(100)
		self.show_msg('Downloading target')

	def download_start(self):
		self._setup_ui()
		self._download_ct = self._ytdl.get_number_of_files_to_download()

		try:
			self._ytdl.download([self._ytdl.get_current_url()])
		except self.Cancelled:
			self.show_msg('Cancelled')
			self.finished(self)
		except Exception as e:
			self.show_msg('Download Error')
			self.error = str(e)
			self.finished(self)
		finally:
			# Needed after every ytdl download to avoid future format collisions
			logging.debug('Cleanup')
			self._ytdl.reset_format()
			self._ytdl.set_progress_hooks([])

	def download_cancel(self):
		self._cancel_flag = True

	def ytdl_processing_hook(self, d: dict):
		"""
		YoutubeDl hook that sometimes gets called during download.
		Refreshes UI, shows progress and throws exception on error.
		"""
		logging.debug('Entered hook')
		if self._cancel_flag:
			raise self.Cancelled
		QApplication.processEvents()
		# Status dictionary
		if d[self._ytdl.Keys.status] == self._ytdl.Keys.downloading:
			total_str = ''
			downloaded = d[self._ytdl.Keys.downloaded_bytes]
			downloaded_str = utils.convert_size(downloaded)
			if self._ytdl.Keys.total_bytes in d:
				total = d[self._ytdl.Keys.total_bytes]
				self.set_pbar_value(floor(downloaded / total * 100))
				total_str = utils.convert_size(total)
			elif self._ytdl.Keys.total_bytes_estimate in d:
				total = d[self._ytdl.Keys.total_bytes_estimate]
				self.set_pbar_value(floor(downloaded / total * 100))
				total_str = utils.convert_size(total)

			msg = ''
			if utils.check_dict_attribute(d, self._ytdl.Keys.eta):
				msg += f"ETA: {str(datetime.timedelta(seconds=d[self._ytdl.Keys.eta]))}    "
			msg += f"{downloaded_str} / {total_str}"
			self.show_msg(msg)

		elif d[self._ytdl.Keys.status] == self._ytdl.Keys.finished:
			self._download_ct = self._download_ct - 1
			if self._download_ct == 0:
				self.file_ready_for_playback(d[self._ytdl.Keys.filename])
				self.show_msg('Download Finished')
				self.finished(self)

		elif d[self._ytdl.Keys.status] == self._ytdl.Keys.error:
			raise Exception('Something happened inside youtube-dl')
