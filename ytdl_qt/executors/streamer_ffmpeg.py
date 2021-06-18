#!/usr/bin/env python3

import logging
import subprocess
import threading
from typing import List

# from PyQt5.QtCore import QProcess

from ytdl_qt import utils
from ytdl_qt.streamer_abstract import StreamerAbstract


class StreamerFfmpeg(StreamerAbstract):
	def __init__(self, ytdl):
		super().__init__(ytdl)
		self._children = []
		self._monitor = None  # for pyprocess

	def _setup_ui(self):
		self.send_msg_cb('Streaming target')

	def stream_start(self):
		assert not self._children

		self._setup_ui()
		self.set_progress_max_cb(0)

		url_list: List[str] = self.ytdl.get_url_selection()
		protocol_list = self.ytdl.get_protocol_selection()
		flv = False
		if ('m3u8_native' in protocol_list) or ('m3u8' in protocol_list):
			flv = True

		ffmpeg_exe = self.ytdl.get_ffmpeg_path()
		assert ffmpeg_exe

		ffmpeg_cmd = [ffmpeg_exe] + utils.build_ffmpeg_args_list(url_list=url_list, flv=flv, quiet=True)
		logging.debug(' '.join(ffmpeg_cmd))

		player_exe = self.ytdl.player_path
		assert player_exe

		player_cmd = [player_exe] + self.ytdl.player_params + ['-']
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
			self.send_msg_cb('Streaming error')
			self.error = str(e)
			if self._monitor is not None:
				self._monitor.join()
			self.finished_cb(self)

	def stream_start_detached(self):
		self._setup_ui()
		url_list: List[str] = self.ytdl.get_url_selection()
		protocol_list: List[str] = self.ytdl.get_protocol_selection()
		flv = False
		if ('m3u8_native' in protocol_list) or ('m3u8' in protocol_list):
			flv = True

		ffmpeg_exe = self.ytdl.get_ffmpeg_path()
		assert ffmpeg_exe

		ffmpeg_cmd = [f'\"{ffmpeg_exe}\"'] + \
			utils.build_ffmpeg_args_list(url_list=url_list, flv=flv, quiet=True, quoted=True)

		player_exe = self.ytdl.player_path
		assert player_exe

		player_cmd = [f'\"{player_exe}\"'] + self.ytdl.player_params + ['-']

		arg_cmd = ffmpeg_cmd + ['|'] + player_cmd
		arg_cmd_str = ' '.join(arg_cmd)
		logging.debug(arg_cmd_str)
		try:
			subprocess.Popen(arg_cmd_str, shell=True, start_new_session=True)
		except Exception as e:
			self.send_msg_cb('Streaming error')
			self.error = str(e)
		self.finished_cb(self)

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
		self.send_msg_cb('Finished streaming')
		self.finished_cb(self)
