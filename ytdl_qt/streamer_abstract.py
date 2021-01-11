#!/usr/bin/env python3

from abc import ABC, abstractmethod

from ytdl_qt.executor_abstract import ExecutorAbstract


class StreamerAbstract(ExecutorAbstract):

	def __init__(self, ytdl, com):
		super().__init__(ytdl, com)

	@abstractmethod
	def stream_start(self):
		pass

	@abstractmethod
	def stream_start_detached(self):
		pass

	@abstractmethod
	def _stream_finish(self):
		pass
