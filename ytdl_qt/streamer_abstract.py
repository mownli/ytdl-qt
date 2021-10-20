#!/usr/bin/env python3

from abc import abstractmethod

from ytdl_qt.executor_abstract import ExecutorAbstract


class StreamerAbstract(ExecutorAbstract):

	def __init__(self, params, ytdl_info):
		super().__init__(params, ytdl_info)

	@abstractmethod
	def stream_start(self):
		pass

	@abstractmethod
	def stream_start_detached(self):
		pass
