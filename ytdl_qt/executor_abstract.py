#!/usr/bin/env python3

from abc import ABC, abstractmethod


class Comm:

	set_pbar_max_cb = None  # (value)
	set_pbar_value_cb = None  # (value)
	show_msg_cb = None  # (msg)
	release_ui_cb = None
	ready_for_playback_cb = None   # (filepath)
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
