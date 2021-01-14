#!/usr/bin/env python3

import logging
import subprocess
import threading

# from PyQt5.QtCore import QProcess

from ytdl_qt.streamer_abstract import StreamerAbstract
from ytdl_qt import utils


class StreamerFfmpeg(StreamerAbstract):
	def __init__(self, ytdl, comm):
		logging.debug('Instantiating StreamerFfmpeg')

		assert comm.show_msg_cb is not None
		assert comm.release_ui_cb is not None
		assert comm.set_pbar_max_cb is not None

		super().__init__(ytdl, comm)
		self._children = []

	def _setup_ui(self):
		self.comm.show_msg_cb('Streaming target')

	def _release_ui(self, msg):
		self.comm.show_msg_cb(msg)
		self.comm.release_ui_cb()

	def stream_start(self):
		assert not self._children

		self._setup_ui()
		self.comm.set_pbar_max_cb(0)

		url_list = self._ytdl.get_url_selection()
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

		ffmpeg = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
		player = subprocess.Popen(player_cmd, stdin=ffmpeg.stdout)

		self._children.append(ffmpeg)
		self._children.append(player)

		self._monitor = threading.Thread(target=self._stream_finish, daemon=True)
		self._monitor.start()

	def stream_start_detached(self):
		url_list = self._ytdl.get_url_selection()
		protocol_list = self._ytdl.get_protocol_selection()
		flv = False
		if ('m3u8_native' in protocol_list) or ('m3u8' in protocol_list):
			flv = True
		ffmpeg_cmd = utils.build_ffmpeg_cmd(url_list=url_list, flv=flv, quiet=True, protected_args=True)
		player_cmd = [utils.Paths.get_mpv_exe(), '--really-quiet', '--force-window=yes', '-']
		arg_cmd = ffmpeg_cmd + ['|'] + player_cmd
		arg_cmd_str = ' '.join(arg_cmd)
		logging.debug(arg_cmd_str)
		subprocess.Popen(arg_cmd_str, shell=True, start_new_session=True)

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
		self._release_ui('Finished streaming')
