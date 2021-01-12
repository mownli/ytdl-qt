#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import Callable


class Comm:

	set_pbar_max_cb = Callable[[int], None]  # (value)
	set_pbar_value_cb = Callable[[int], None]  # (value)
	show_msg_cb = Callable[[str], None]  # (msg)
	release_ui_cb = Callable[[], None]
	ready_for_playback_cb = Callable[[str], None]   # (filepath)
	# TODO: add error signal


class ExecutorAbstract(ABC):

	process_timeout = 5000  # ms

	def __init__(self, ytdl, comm):
		self._ytdl = ytdl
		self.comm = comm

	@abstractmethod
	def _setup_ui(self):
		pass

	@abstractmethod
	def _release_ui(self, msg):
		self.comm.release_ui_cb()
