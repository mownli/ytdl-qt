#!/usr/bin/env python3

import logging
import subprocess
import threading

# from PyQt5.QtCore import QProcess

from ytdl_qt.downloader_abstract import DownloaderAbstract
from ytdl_qt import utils


class DownloaderFfmpeg(DownloaderAbstract):
	def __init__(self, ytdl):
		super().__init__(ytdl)
		self._child = None
		self._cancel_flag: bool = False

	def _setup_ui(self):
		self.set_progress_max_cb(0)
		self.send_msg_cb('Downloading target')

	def download_start(self):
		"""Download with ffmpeg. Useful for m3u8 protocol. Doesn't block."""
		assert self._child is None

		self._setup_ui()

		path, ext = self.ytdl.get_filename()
		ext = '.mkv'
		filepath = ''.join([path, ext])

		exe = self.ytdl.get_ffmpeg_path()
		assert exe

		cmd = [exe] + \
			utils.build_ffmpeg_args_list(self.ytdl.get_url_selection(), output_file=filepath)
		logging.debug(f"Command line list: {cmd}")
		logging.debug(f"Command line: {' '.join(cmd)}")
		# logging.debug(f"Command line: {cmd}")

		# subproc = QProcess()
		# subproc.finished.connect(self._download_finish)
		# subproc.start(cmd[0], cmd[1:])
		# if not subproc.waitForStarted(self.process_timeout):
		# 	subproc.kill()
		# 	self._release_ui('Download error')
		# 	raise Exception('FFmpeg execution error')

		#subproc = subprocess.Popen(' '.join(cmd), shell=True)
		try:
			subproc = subprocess.Popen(cmd)
			self._child = subproc
			self._monitor = threading.Thread(target=self._download_finish, daemon=True)
			self._monitor.start()
		except Exception as e:
			self.send_msg_cb('Download error')
			self.error = str(e)
			self.finished_cb(self)
			return

		self.file_ready_for_playback_cb(filepath)

	def download_cancel(self):
		assert self._child is not None
		self._cancel_flag = True
		self._child.terminate()
		logging.debug('Sent SIGTERM to subprocess')
		self.send_msg_cb('Cancelled')
		self.finished_cb(self)

	# def _download_finish(self):
	# 	# Relies on QProcess
	# 	if not self._cancel_flag:
	# 		ret = self._child.exitCode()
	# 		if ret == 0:
	# 			self._release_ui('Download Finished')
	# 		else:
	# 			self._release_ui(f'FFmpeg Error. Exit code {ret}')

	def _download_finish(self):
		self._child.wait()
		if not self._cancel_flag:
			ret = self._child.returncode
			if ret == 0:
				self.send_msg_cb('Download Finished')
			else:
				self.send_msg_cb('Download error')
				self.error = f'FFmpeg Error. Exit code {ret}'
			self.finished_cb(self)
