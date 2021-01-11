#!/usr/bin/env python3

from abc import ABC, abstractmethod

from PyQt5.QtCore import pyqtSignal, QObject


class DownloaderAbstract(ABC):

	process_timeout = 5000 # ms

	class Messenger(QObject):
		set_pbar_max_signal = pyqtSignal(int)
		set_pbar_value_signal = pyqtSignal(int)
		show_msg_signal = pyqtSignal(str)
		release_signal = pyqtSignal()
		ready_for_playback_signal = pyqtSignal(str)
		# TODO: add error signal

		def __init__(self):
			super().__init__()

	def __init__(self, ytdl):
		self._ytdl = ytdl
		self.com = self.Messenger()

	@abstractmethod
	def _setup_ui(self):
		pass

	@abstractmethod
	def _release_ui(self, msg):
		pass

	@abstractmethod
	def download_start(self):
		pass

	@abstractmethod
	def download_cancel(self):
		pass

	@abstractmethod
	def _download_finish(self):
		pass

	@abstractmethod
	def stream_start(self):
		pass

	@abstractmethod
	def _stream_finish(self):
		pass
