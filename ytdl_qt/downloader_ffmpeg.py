#!/usr/bin/env python3

import logging
from subprocess import Popen

from PyQt5.QtCore import QProcess

from ytdl_qt.downloader_abstract import DownloaderAbstract
from ytdl_qt import utils


class DownloaderFfmpeg(DownloaderAbstract):
	def __init__(self, ytdl):
		logging.debug('Instantiating DownloaderFfmpeg')
		super().__init__(ytdl)
		self._child_d = None
		self._children_s = []
		self._cancel_flag = False

	def _setup_ui(self):
		self.com.set_pbar_max_signal.emit(0)
		self.com.show_msg_signal.emit('Downloading target')

	def _release_ui(self, msg):
		self.com.show_msg_signal.emit(msg)
		self.com.release_signal.emit()

	def download_start(self):
		"""Download with ffmpeg. Useful for m3u8 protocol. Doesn't block."""
		assert self._child_d is None
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
		self._child_d = subproc

		self.com.ready_for_playback_signal.emit(filepath)

	def download_cancel(self):
		assert self._child_d is not None
		self._cancel_flag = True
		self._child_d.terminate()
		logging.debug('Sent SIGTERM to subprocess')
		self._release_ui('Cancelled')

	def _download_finish(self):
		if not self._cancel_flag:
			ret = self._child_d.exitCode()
			if ret == 0:
				self._release_ui('Download Finished')
			else:
				self._release_ui(f'FFmpeg Error. Exit code {ret}')
				# TODO: error
				# raise Exception(f'FFMPEG Error. Exit code {ret}')

	def stream_start(self):
		assert not self._children_s
		url_list = self._ytdl.get_url_selection()
		protocol_list = self._ytdl.get_protocol_selection()
		flv = False
		if ('m3u8_native' in protocol_list) or ('m3u8' in protocol_list):
			flv = True
		ffmpeg_cmd = utils.build_ffmpeg_cmd(url_list=url_list, flv=flv, quiet=True)
		logging.debug(' '.join(ffmpeg_cmd))
		player_cmd = [utils.Paths.get_mpv_exe(), '--really-quiet', '--force-window=yes', '-']
		logging.debug(' '.join(player_cmd))

		ffmpeg = QProcess()
		ffmpeg.setProgram(ffmpeg_cmd[0])
		ffmpeg.setArguments(ffmpeg_cmd[1:])

		player = QProcess()
		player.setProgram(player_cmd[0])
		player.setArguments(player_cmd[1:])
		player.finished.connect(self._stream_finish)

		ffmpeg.setStandardOutputProcess(player)

		ffmpeg.start()
		player.start()

		if not ffmpeg.waitForStarted(self.process_timeout):
			ffmpeg.kill()
			player.kill()
			raise Exception('FFmpeg execution error')
		if not player.waitForStarted(self.process_timeout):
			ffmpeg.kill()
			player.kill()
			raise Exception('Player execution error')

		self._children_s.append(ffmpeg)
		self._children_s.append(player)

	def stream_start_detached(self):
		url_list = self._ytdl.get_url_selection()
		protocol_list = self._ytdl.get_protocol_selection()
		flv = False
		if ('m3u8_native' in protocol_list) or ('m3u8' in protocol_list):
			flv = True
		ffmpeg_cmd = utils.build_ffmpeg_cmd(url_list=url_list, flv=flv, quiet=True)
		player_cmd = [utils.Paths.get_mpv_exe(), '--really-quiet', '--force-window=yes', '-']
		arg_cmd = ffmpeg_cmd + ['|'] + player_cmd
		arg_cmd_str = ' '.join(arg_cmd)
		logging.debug(arg_cmd_str)
		Popen(arg_cmd_str, shell=True, start_new_session=True)

	def _stream_finish(self):
		if self._children_s:
			self._children_s[0].terminate()
			logging.debug('Sent SIGTERM to subprocess')
		# TODO: Error message
