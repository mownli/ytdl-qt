#!/usr/bin/env python3

from abc import abstractmethod

from ytdl_qt.ytdl import Ytdl
from ytdl_qt.executor_abstract import ExecutorAbstract


class StreamerAbstract(ExecutorAbstract):

	def __init__(self, ytdl: Ytdl):
		super().__init__(ytdl)

	@abstractmethod
	def stream_start(self):
		pass

	@abstractmethod
	def stream_start_detached(self):
		pass
