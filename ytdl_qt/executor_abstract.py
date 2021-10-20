#!/usr/bin/env python3

from __future__ import annotations  # in 3.10 gets into the mainline
from abc import ABC, abstractmethod

from ytdl_qt.ytdl_info import Info
from ytdl_qt.core_params import CoreParams


class ExecutorAbstract(ABC):

	process_timeout: int = 5000  # ms
	error: str = ''

	def __init__(self, params: CoreParams, ytdl_info: Info):
		assert params is not None
		assert ytdl_info is not None
		self.params: CoreParams = params
		self.ytdl_info: Info = ytdl_info

	@abstractmethod
	def _setup_ui(self):
		pass

	def update_ui_cb(self):
		pass

	def set_progress_max_cb(self, val: int):
		pass

	def set_progress_val_cb(self, val: int):
		pass

	def send_msg_cb(self, msg: str):
		pass

	def finished_cb(self, sender: ExecutorAbstract):
		pass
