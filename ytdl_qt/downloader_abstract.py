#!/usr/bin/env python3

from abc import ABC, abstractmethod

from ytdl_qt.executor_abstract import ExecutorAbstract


class DownloaderAbstract(ExecutorAbstract):

	def __init__(self, ytdl, com):
		super().__init__(ytdl, com)

	@abstractmethod
	def download_start(self):
		pass

	@abstractmethod
	def download_cancel(self):
		pass

	@abstractmethod
	def _download_finish(self):
		pass
