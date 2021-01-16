#!/usr/bin/env python3

import logging
import subprocess
import threading

# from PyQt5.QtCore import QProcess
from typing import List

from ytdl_qt.streamer_abstract import StreamerAbstract
from ytdl_qt import utils


class StreamerFfmpeg(StreamerAbstract):
	def __init__(self, ytdl):
		logging.debug('Instantiating StreamerFfmpeg')
		super().__init__(ytdl)
		self._children = []
		self._monitor = None  # for pyprocess

	def _setup_ui(self):
		self.show_msg('Streaming target')

	def stream_start(self):
		assert not self._children

		self._setup_ui()
		self.set_pbar_max(0)

		url_list: List[str] = self._ytdl.get_url_selection()
		protocol_list = self._ytdl.get_protocol_selection()
		flv = False
		if ('m3u8_native' in protocol_list) or ('m3u8' in protocol_list):
			flv = True
		ffmpeg_cmd = utils.build_ffmpeg_cmd(url_list=url_list, flv=flv, quiet=True)
		logging.debug(' '.join(ffmpeg_cmd))
		player_cmd = [utils.Paths.get_mpv_exe(), '--really-quiet', '--force-window=yes', '-']
		logging.debug(' '.join(player_cmd))

		# ffmpeg = QProcess()
		# ffmpeg.setProgram(ffmpeg_cmd[0])
		# ffmpeg.setArguments(ffmpeg_cmd[1:])
		#
		# player = QProcess()
		# player.setProgram(player_cmd[0])
		# player.setArguments(player_cmd[1:])
		# player.finished.connect(self._stream_finish)
		#
		# ffmpeg.setStandardOutputProcess(player)
		#
		# ffmpeg.start()
		# player.start()
		#
		# if not ffmpeg.waitForStarted(self.process_timeout):
		# 	ffmpeg.kill()
		# 	player.kill()
		# 	raise Exception('FFmpeg execution error')
		# if not player.waitForStarted(self.process_timeout):
		# 	ffmpeg.kill()
		# 	player.kill()
		# 	raise Exception('Player execution error')

		# ffmpeg = subprocess.Popen(' '.join(ffmpeg_cmd), shell=True, stdout=subprocess.PIPE)
		# player = subprocess.Popen(' '.join(player_cmd), shell=True, stdin=ffmpeg.stdout)

		try:
			ffmpeg = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
			player = subprocess.Popen(player_cmd, stdin=ffmpeg.stdout)

			self._children.append(ffmpeg)
			self._children.append(player)

			self._monitor = threading.Thread(target=self._stream_finish, daemon=True)
			self._monitor.start()
		except Exception as e:
			self.show_msg('Streaming error')
			self.error = str(e)
			if self._monitor is not None:
				self._monitor.join()
			self.finished(self)

	def stream_start_detached(self):
		self._setup_ui()
		url_list: List[str] = self._ytdl.get_url_selection()
		protocol_list: List[str] = self._ytdl.get_protocol_selection()
		flv = False
		if ('m3u8_native' in protocol_list) or ('m3u8' in protocol_list):
			flv = True
		ffmpeg_cmd: List[str] = utils.build_ffmpeg_cmd(url_list=url_list, flv=flv, quiet=True, protected_args=True)
		player_cmd = [utils.Paths.get_mpv_exe(), '--really-quiet', '--force-window=yes', '-']
		arg_cmd = ffmpeg_cmd + ['|'] + player_cmd
		arg_cmd_str = ' '.join(arg_cmd)
		logging.debug(arg_cmd_str)
		try:
			subprocess.Popen(arg_cmd_str, shell=True, start_new_session=True)
		except Exception as e:
			self.show_msg('Streaming error')
			self.error = str(e)
		self.finished(self)

	# def _stream_finish(self):
		# Relies on QProcess
	# 	if self._children:
	# 		self._children[0].terminate()
	# 		logging.debug('Sent SIGTERM to subprocess')
	# 	self._release_ui('Finished streaming')

	def _stream_finish(self):
		if self._children:
			self._children[1].wait()
			self._children[0].stdout.close()
			self._children[0].wait()
		logging.debug('Sent SIGTERM to subprocess')
		self.show_msg('Finished streaming')
		self.finished(self)
