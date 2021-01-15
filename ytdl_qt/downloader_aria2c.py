#!/usr/bin/env python3

import logging
import os

from PyQt5.QtCore import QProcess
import subprocess
import threading

from ytdl_qt.downloader_abstract import DownloaderAbstract
from ytdl_qt import utils


class DownloaderAria2c(DownloaderAbstract):

	def __init__(self, ytdl, comm):
		logging.debug('Instantiating DownloaderAria2c')

		assert comm.set_pbar_max_cb is not None
		assert comm.show_msg_cb is not None
		assert comm.release_ui_cb is not None
		assert comm.ready_for_playback_cb is not None

		super().__init__(ytdl, comm)
		self._child = None
		self._cancel_flag = False
		self._merging = False
		self._files_to_merge = []
		self._final_filepath = None

	def _setup_ui(self):
		self.comm.set_pbar_max_cb(0)
		self.comm.show_msg_cb('Downloading target')

	def _release_ui(self, msg: str):
		self.comm.show_msg_cb(msg)
		self.comm.release_ui_cb()

	def download_start(self):
		"""Download with aria2 (doesn't block)."""
		assert self._child is None
		self._setup_ui()

		cmd = [
			utils.Paths.get_aria2c_exe(), '-c', '-x', '3', '-k', '1M',
			'--summary-interval=1', '--enable-color=false', '--file-allocation=falloc'
		]

		url_list = self._ytdl.get_url_selection()

		aria2_input = ''
		if len(url_list) == 1:
			single = True
			name, ext = self._ytdl.get_filename()
			file = name + ext
			self._final_filepath = file
			url = ''.join(url_list)
			logging.debug(file)
			cmd += ['-o', f"{file}", f"{url}"]
		else:
			single = False
			name = self._ytdl.get_filename()[0]
			fmts = self._ytdl.fmt_id_selection
			for index, url in enumerate(url_list):
				path = f"{name}.{fmts[index]}.input{index}"
				aria2_input += url + f"\n out={path}\n"
				self._files_to_merge.append(path)
			cmd += ['-i', '-']
		logging.debug(f"Command line {' '.join(cmd)}")

		# If you use this, comment out self.wait() at the top of self._download_finish
		# self.exec_qprocess_download(cmd, single, aria2_input)

		self._exec_pyprocess_download(cmd, single, aria2_input)

	def _exec_qprocess_download(self, cmd: list, single: bool, aria2_input: str):
		subproc = QProcess()
		subproc.finished.connect(self._download_finish)
		subproc.start(cmd[0], cmd[1:])
		if not subproc.waitForStarted(self.process_timeout):  # timeout in ms
			subproc.kill()
			self._release_ui('Download error')
			raise Exception('aria2c execution error')
		if not single:
			subproc.write(aria2_input.encode())
			subproc.closeWriteChannel()

		self._child = subproc

	def _exec_pyprocess_download(self, cmd: list, single: bool, aria2_input: str):
		try:
			subproc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
		except Exception:
			self._release_ui('Download error')
			raise
		if not single:
			subproc.communicate(aria2_input.encode())
			subproc.stdin.close()
		self._child = subproc

		self._monitor = threading.Thread(target=self._download_finish, daemon=True)
		self._monitor.start()

	def download_cancel(self):
		assert self._child is not None
		self._cancel_flag = True
		self._child.terminate()
		logging.debug('Sent SIGTERM to subprocess')
		self._release_ui('Cancelled')

	def _download_finish(self):
		self._child.wait()  # for pyprocess only
		if not self._cancel_flag:
			ret = self._child.returncode
			if ret == 0:

				def good_end():
					self.comm.ready_for_playback_cb(self._final_filepath)
					self._release_ui('Download Finished')

				if self._merging:
					for file in self._files_to_merge:
						os.remove(file)
						logging.debug(f'Removed temporary file: {file}')
					good_end()
				else:
					if self._files_to_merge:
						self._merge_files()
					else:
						good_end()
			else:
				if self._merging:
					self._release_ui(f'FFmpeg Error. Exit code {ret}')
				else:
					self._release_ui(f'aria2c Error. Exit code {ret}')

	def _merge_files(self):
		"""Merge outputs."""
		assert self._files_to_merge
		self._merging = True
		self.comm.show_msg_cb('Merging files')

		name = self._ytdl.get_filename()[0]
		filepath = f"{name}.mkv"
		cmd = utils.build_ffmpeg_cmd(self._files_to_merge, output_file=filepath, protected_args=True)
		logging.debug(f"Command line {cmd}")

		# subproc = QProcess()
		# subproc.finished.connect(self._download_finish)
		# subproc.start(cmd[0], cmd[1:])
		# if not subproc.waitForStarted(self.process_timeout):  # timeout in ms
		# 	subproc.kill()
		# 	self._release_ui('FFMPEG execution error')

		try:
			subproc = subprocess.Popen(' '.join(cmd), shell=True)
		except Exception:
			self._release_ui('Merging error')
			raise

		self._child = subproc

		self._monitor = threading.Thread(target=self._download_finish, daemon=True)
		self._monitor.start()

		self._final_filepath = filepath
