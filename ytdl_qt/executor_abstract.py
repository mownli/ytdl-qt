#!/usr/bin/env python3

from __future__ import annotations  # in 3.10 gets into the mainline
from abc import ABC, abstractmethod

from ytdl_qt.ytdl import Ytdl


class ExecutorAbstract(ABC):

	process_timeout: int = 5000  # ms
	error: str = ''

	def __init__(self, ytdl: Ytdl):
		self._ytdl = ytdl

	@abstractmethod
	def _setup_ui(self):
		pass

	def set_pbar_max(self, val: int):
		raise NotImplementedError

	def set_pbar_value(self, val: int):
		raise NotImplementedError

	def show_msg(self, msg: str):
		raise NotImplementedError

	def finished(self, sender: ExecutorAbstract):
		raise NotImplementedError
