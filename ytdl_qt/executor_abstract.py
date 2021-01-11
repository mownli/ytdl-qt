#!/usr/bin/env python3

from abc import ABC, abstractmethod


class Com:
	set_pbar_max_cb = None
	set_pbar_value_cb = None
	show_msg_cb = None
	release_ui_cb = None
	ready_for_playback_cb = None
	# TODO: add error signal


class ExecutorAbstract(ABC):

	process_timeout = 5000  # ms

	def __init__(self, ytdl, com):
		self._ytdl = ytdl
		self.com = com

	@abstractmethod
	def _setup_ui(self):
		pass

	@abstractmethod
	def _release_ui(self, msg):
		self.com.release_ui_cb()
