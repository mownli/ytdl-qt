#!/usr/bin/env python3

from abc import abstractmethod

from ytdl_qt.executor_abstract import ExecutorAbstract


class DownloaderAbstract(ExecutorAbstract):

	def __init__(self, ytdl, comm):
		super().__init__(ytdl, comm)

	@abstractmethod
	def download_start(self):
		pass

	@abstractmethod
	def download_cancel(self):
		pass

	@abstractmethod
	def _download_finish(self):
		pass
