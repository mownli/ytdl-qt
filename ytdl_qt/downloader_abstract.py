#!/usr/bin/env python3

from abc import abstractmethod

from ytdl_qt.ytdl import Ytdl
from ytdl_qt.executor_abstract import ExecutorAbstract


class DownloaderAbstract(ExecutorAbstract):

	def __init__(self, ytdl: Ytdl):
		super().__init__(ytdl)

	@abstractmethod
	def download_start(self):
		pass

	@abstractmethod
	def download_cancel(self):
		pass

	def file_ready_for_playback_cb(self, path: str):
		pass
