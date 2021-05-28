#!/usr/bin/env python3

import logging
import subprocess
from enum import Enum, auto

from ytdl_qt.executor_abstract import ExecutorAbstract
from ytdl_qt.streamer_abstract import StreamerAbstract
from ytdl_qt.downloader_abstract import DownloaderAbstract
from ytdl_qt.executors.streamer_ffmpeg import StreamerFfmpeg
from ytdl_qt.executors.downloader_aria2c import DownloaderAria2c
from ytdl_qt.executors.downloader_ffmpeg import DownloaderFfmpeg
from ytdl_qt.executors.downloader_ytdl import DownloaderYtdl
from ytdl_qt.ytdl import Ytdl
from ytdl_qt import utils


class Callbacks:

	def task_finished_cb(self, signal: tuple[bool, str]) -> None:
		pass

	def playback_enabled_cb(self) -> None:
		pass

	def redraw_cb(self) -> None:
		pass

	def set_progress_max_cb(self, val: int) -> None:
		pass

	def set_progress_val_cb(self, val: int) -> None:
		pass

	def show_msg_cb(self, msg: str) -> None:
		pass


class Core(Callbacks):

	class DownloaderType(Enum):
		YTDL = auto()
		FFMPEG = auto()
		ARIA2 = auto()

	def __init__(self):
		self.ytdl: Ytdl = Ytdl()
		self.downloader = None
		self.streamer_list = []

		self.d_blocked = False
		self.file_for_playback: str = ''

	def download_info(self, url: str) -> None:
		self.ytdl.download_info(url)
		self.file_for_playback = ''

	def get_info(self):
		return self.ytdl.get_info()

	def get_title(self):
		return self.ytdl.get_title()

	def set_playback_enabled(self, path: str) -> None:
		"""Enable playButton for file playback."""
		logging.debug(f'Filepath = {path}')
		self.file_for_playback = path
		self.playback_enabled_cb()

	def is_download_blocked(self) -> bool:
		return self.d_blocked

	def set_format(self, fmt_id_list) -> None:
		self.ytdl.set_format(fmt_id_list)

	def download_with_ffmpeg(self) -> None:
		self.download_target(self.DownloaderType.FFMPEG)

	def download_with_ytdl(self) -> None:
		self.download_target(self.DownloaderType.YTDL)

	def download_with_aria2(self) -> None:
		self.download_target(self.DownloaderType.ARIA2)

	def download_target(self, d_type: DownloaderType) -> None:
		"""Run selected downloader."""
		if d_type is self.DownloaderType.YTDL:
			self.downloader = DownloaderYtdl(self.ytdl)
		elif d_type is self.DownloaderType.FFMPEG:
			self.downloader = DownloaderFfmpeg(self.ytdl)
		elif d_type is self.DownloaderType.ARIA2:
			self.downloader = DownloaderAria2c(self.ytdl)

		# self.ytdl.set_format(self.get_selected_formats_cb())

		self.connect_downloader(self.downloader)
		self.d_blocked = True
		self.downloader.download_start()

	def stream_target(self) -> None:
		self.streamer_list.append(StreamerFfmpeg(self.ytdl))
		self.connect_streamer(self.streamer_list[-1])
		# self.ytdl.set_format(self.get_selected_formats_cb)
		# self.streamer_list[-1].stream_start()
		self.streamer_list[-1].stream_start_detached()

	def play_target(self) -> None:
		assert self.file_for_playback
		logging.debug(f'Playing {self.file_for_playback}')
		subprocess.Popen(
			[utils.Paths.get_mpv_exe(), '--force-window', '--quiet', self.file_for_playback]
		)

	def download_cancel(self) -> None:
		self.downloader.download_cancel()

	def connect_downloader(self, downloader: DownloaderAbstract) -> None:
		downloader.update_ui_cb = self.redraw_cb
		downloader.set_progress_max_cb = self.set_progress_max_cb
		downloader.set_progress_val_cb = self.set_progress_val_cb
		downloader.show_msg_cb = self.show_msg_cb

		downloader.finished_cb = self.task_finished_cb
		downloader.file_ready_for_playback_cb = self.playback_enabled_cb

	def connect_streamer(self, downloader: StreamerAbstract) -> None:
		downloader.set_progress_max_cb = self.set_progress_max_cb
		downloader.show_msg_cb = self.show_msg_cb
		downloader.finished_cb = self.task_finished_cb

	def task_finished(self, sender: ExecutorAbstract) -> None:
		self.d_blocked = False
		signal = (False if sender.error else True, sender.error)
		self.task_finished_cb(signal)
