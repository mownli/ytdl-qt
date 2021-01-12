#!/usr/bin/env python3

import logging

from PyQt5.QtCore import QProcess

from ytdl_qt.downloader_abstract import DownloaderAbstract
from ytdl_qt import utils


class DownloaderFfmpeg(DownloaderAbstract):
	def __init__(self, ytdl, comm):
		logging.debug('Instantiating DownloaderFfmpeg')

		assert comm.set_pbar_max_cb is not None
		assert comm.show_msg_cb is not None
		assert comm.release_ui_cb is not None
		assert comm.ready_for_playback_cb is not None

		super().__init__(ytdl, comm)
		self._child = None
		self._cancel_flag = False

	def _setup_ui(self):
		self.comm.set_pbar_max_cb(0)
		self.comm.show_msg_cb('Downloading target')

	def _release_ui(self, msg):
		self.comm.show_msg_cb(msg)
		self.comm.release_ui_cb()

	def download_start(self):
		"""Download with ffmpeg. Useful for m3u8 protocol. Doesn't block."""
		assert self._child is None
		self._setup_ui()

		# filename = ''.join(list(self._ytdl.get_filename()))
		path, ext = self._ytdl.get_filename()
		ext = '.mkv'
		filepath = ''.join([path, ext])
		cmd = utils.build_ffmpeg_cmd(self._ytdl.get_url_selection(), output_file=filepath)
		logging.debug(f"Command line {cmd}")

		subproc = QProcess()
		subproc.finished.connect(self._download_finish)
		subproc.start(cmd[0], cmd[1:])
		if not subproc.waitForStarted(self.process_timeout):
			subproc.kill()
			self._release_ui('Download error')
			raise Exception('FFmpeg execution error')
		self._child = subproc

		self.comm.ready_for_playback_cb(filepath)

	def download_cancel(self):
		assert self._child is not None
		self._cancel_flag = True
		self._child.terminate()
		logging.debug('Sent SIGTERM to subprocess')
		self._release_ui('Cancelled')

	def _download_finish(self):
		if not self._cancel_flag:
			ret = self._child.exitCode()
			if ret == 0:
				self._release_ui('Download Finished')
			else:
				self._release_ui(f'FFmpeg Error. Exit code {ret}')
				# TODO: error
				# raise Exception(f'FFMPEG Error. Exit code {ret}')
