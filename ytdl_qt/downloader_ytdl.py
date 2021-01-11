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

	def __init__(self, ytdl, com):
		logging.debug('Instantiating DownloaderYtdl')

		assert com.set_pbar_max_cb is not None
		assert com.show_msg_cb is not None
		assert com.release_ui_cb is not None
		assert com.set_pbar_value_cb is not None
		assert com.ready_for_playback_cb is not None

		super().__init__(ytdl, com)
		self._ytdl.add_progress_hook(self.ytdl_processing_hook)
		self._download_ct = 0
		self._cancel_flag = False

	def _setup_ui(self):
		self.com.set_pbar_max_cb(100)
		self.com.show_msg_cb('Downloading target')

	def _release_ui(self, msg):
		self.com.show_msg_cb(msg)
		self.com.release_ui_cb()

	def download_start(self):
		""""""
		self._setup_ui()
		self._download_ct = self._ytdl.get_number_of_files_to_download()

		try:
			self._ytdl.download([self._ytdl.get_current_url()])
		except self.Cancelled:
			self._release_ui('Cancelled')
		except Exception as e:
			self._release_ui('Error')
			raise e
		finally:
			# Needed after every ytdl download to avoid future format collisions
			logging.debug('Cleanup')
			self._ytdl.reset_format()
			self._ytdl.set_progress_hooks([])

	def download_cancel(self):
		self._cancel_flag = True

	def _download_finish(self):
		pass

	def ytdl_processing_hook(self, d):
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
				self.com.set_pbar_value_cb(floor(downloaded / total * 100))
				total_str = utils.convert_size(total)
			elif self._ytdl.Keys.total_bytes_estimate in d:
				total = d[self._ytdl.Keys.total_bytes_estimate]
				self.com.set_pbar_value_cb(floor(downloaded / total * 100))
				total_str = utils.convert_size(total)

			msg = ''
			if utils.check_dict_attribute(d, self._ytdl.Keys.eta):
				msg += f"ETA: {str(datetime.timedelta(seconds=d[self._ytdl.Keys.eta]))}    "
			msg += f"{downloaded_str} / {total_str}"
			self.com.show_msg_cb(msg)

		elif d[self._ytdl.Keys.status] == self._ytdl.Keys.finished:
			self.com.ready_for_playback_cb(d[self._ytdl.Keys.filename])
			self._release_ui('Download Finished')
		elif d[self._ytdl.Keys.status] == self._ytdl.Keys.error:
			raise Exception('Something happened')
