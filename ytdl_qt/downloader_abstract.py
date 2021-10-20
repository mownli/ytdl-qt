#!/usr/bin/env python3

from abc import abstractmethod

from ytdl_qt.executor_abstract import ExecutorAbstract


class DownloaderAbstract(ExecutorAbstract):

	def __init__(self, params, ytdl_info):
		super().__init__(params, ytdl_info)

	@abstractmethod
	def download_start(self):
		pass

	@abstractmethod
	def download_cancel(self):
		pass

	def file_ready_for_playback_cb(self, path: str):
		pass
