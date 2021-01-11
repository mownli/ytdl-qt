#!/usr/bin/env python3

import logging
import os

from PyQt5.QtCore import QProcess

from ytdl_qt.downloader_abstract import DownloaderAbstract
from ytdl_qt import utils


class DownloaderAria2c(DownloaderAbstract):

	def __init__(self, ytdl, com):
		logging.debug('Instantiating DownloaderAria2c')

		assert com.set_pbar_max_cb is not None
		assert com.show_msg_cb is not None
		assert com.release_ui_cb is not None
		assert com.ready_for_playback_cb is not None

		super().__init__(ytdl, com)
		self._child = None
		self._cancel_flag = False
		self._merging = False
		self._files_to_merge = []
		self._final_filepath = None

	def _setup_ui(self):
		self.com.set_pbar_max_cb(0)
		self.com.show_msg_cb('Downloading target')

	def _release_ui(self, msg):
		self.com.show_msg_cb(msg)
		self.com.release_ui_cb()

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
			file = ''.join(list(self._ytdl.get_filename()))
			self._final_filepath = file
			url = ''.join(url_list)
			logging.debug(file)
			cmd += ['-o', file, url]
		else:
			single = False
			name = self._ytdl.get_filename()[0]
			for index, url in enumerate(url_list):
				aria2_input += url + f"\n out={name}.input{index}\n"
				self._files_to_merge.append(f"{name}.input{index}")
			cmd += ['-i', '-']
		logging.debug(f"Command line {' '.join(cmd)}")

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
				def good_end():
					self.com.ready_for_playback_cb(self._final_filepath)
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
				# TODO: error
				# raise Exception(f'Error.Exit code {ret}')

	def _merge_files(self):
		"""Merge outputs."""
		assert self._files_to_merge
		self._merging = True
		self.com.show_msg_cb('Merging files')

		filepath = ''.join(list(self._ytdl.get_filename()))
		cmd = utils.build_ffmpeg_cmd(self._files_to_merge, output_file=filepath)
		logging.debug(f"Command line {cmd}")

		subproc = QProcess()
		subproc.finished.connect(self._download_finish)
		subproc.start(cmd[0], cmd[1:])
		if not subproc.waitForStarted(self.process_timeout):  # timeout in ms
			subproc.kill()
			self._release_ui('FFMPEG execution error')
			# TODO: error
			# raise Exception('FFMPEG execution error')
		self._child = subproc
		self._final_filepath = filepath
