#!/usr/bin/env python3

import logging
import subprocess

import ytdl_qt.executor_abstract as ExAbs
from ytdl_qt.streamer_ffmpeg import StreamerFfmpeg
from ytdl_qt.downloader_aria2c import DownloaderAria2c
from ytdl_qt.downloader_ffmpeg import DownloaderFfmpeg
from ytdl_qt.downloader_ytdl import DownloaderYtdl
from ytdl_qt.qt_historytablemodel import HistoryTableModel
from ytdl_qt.ytdl import Ytdl
from ytdl_qt.qt_mainwindow import MainWindow
from ytdl_qt import utils


class Core:

	window_title = 'ytdl-qt'

	def __init__(self, url):

		self.ytdl = Ytdl()
		self.downloader = None
		self.streamer_list = []

		self.ui = self.make_ui()
		self.ui.set_window_title(self.window_title)
		self.ui.show()
		self.exec_comm = self.make_exec_comm()

		self.d_blocked = False
		self.file_for_playback = None

		try:
			self.load_history(utils.Paths.get_history())
		except Exception as e:
			logging.debug("Failed to load history")
			raise e

		if url is not None:
			self.ui.urlEdit_set_text(url)
			self.download_info(url)

		# if url is not None:
			# 	# Slot is called after the window is shown
			# 	QTimer.singleShot(0, self.get_info_auto_slot)
			# 	self.url_from_stdin = url
			# 	self.ui.urlEdit_set_text(self.url_from_stdin)

	def make_exec_comm(self):
		ec = ExAbs.Comm()
		ec.set_pbar_max_cb = self.ui.set_progressBar_max  # (value)
		ec.set_pbar_value_cb = self.ui.set_progressBar_value  # (value)
		ec.show_msg_cb = self.ui.show_status_msg  # (msg)
		ec.release_ui_cb = self.release_ui
		ec.ready_for_playback_cb = self.set_playback_enabled  # (filepath)
		return ec

	def make_ui(self):
		mw_comm = MainWindow.Comm()
		mw_comm.get_info_cb = self.download_info
		mw_comm.is_d_blocked_cb = self.is_d_blocked
		mw_comm.download_cb = self.download_target
		mw_comm.cancelled_cb = self.download_cancel
		mw_comm.stream_cb = self.stream_target
		mw_comm.play_cb = self.play_file
		return MainWindow(mw_comm)

	def download_info(self, url):
		"""
		Download URL info, update tableWidget and history, reset playback
		information on success. Blocks UI.
		"""
		logging.debug(f"Loading info for {url}")
		assert url is not None
		self.ui.block_ui()
		self.ui.show_status_msg('Downloading info')
		self.ui.update()

		try:
			self.ytdl.download_info(url)

			self.file_for_playback = None
			self.ui.update_table(self.ytdl.get_info())
			self.ui.playButton_set_disabled()
			self.ui.set_window_title(self.window_title + ' :: ' + self.ytdl.get_title())
			self.ui.show_status_msg('Info loaded')

			self.ui.history_add_item(self.ytdl.get_title(), url)
		except Exception as e:
			self.ui.error_dialog_exec('Info loading error', str(e))
			self.ui.show_status_msg('Info loading error')

		self.ui.unblock_ui()

	def set_playback_enabled(self, path):
		"""Enable playButton for file playback."""
		logging.debug('')
		assert path is not None
		self.file_for_playback = path
		self.ui.set_playButton_enabled(True)

	def release_ui(self):
		self.d_blocked = False
		self.ui.set_window_title(self.window_title + ' :: ' + self.ytdl.get_title())
		self.ui.release_ui()

	def load_history(self, path):
		"""Try to load history from path."""
		logging.debug('Trying to load history')

		history_model = HistoryTableModel(path)
		self.ui.set_history_model(history_model)
		logging.debug('History loaded')

	# def get_info_auto_slot(self):
	# 	self.download_info(self.url_from_stdin)

	def is_d_blocked(self):
		return self.d_blocked

	def download_target(self):
		"""Run selected downloader."""
		# if not self.process_filename():
		# 	return

		if self.ui.is_ytdl_checked():
			self.downloader = DownloaderYtdl(self.ytdl, self.exec_comm)
		elif self.ui.is_ffmpeg_checked():
			self.downloader = DownloaderFfmpeg(self.ytdl, self.exec_comm)
		elif self.ui.is_aria2_checked():
			self.downloader = DownloaderAria2c(self.ytdl, self.exec_comm)

		try:
			self.ytdl.set_format(self.ui.get_selected_fmt_id_list())
			self.d_blocked = True
			self.ui.setup_ui_for_download()
			self.ui.set_window_title(
				self.window_title + ' :: Downloading :: ' + self.ytdl.get_title()
			)
			self.downloader.download_start()
		except Exception as e:
			self.ui.error_dialog_exec('Download Error', str(e))

	def stream_target(self):
		self.streamer_list.append(StreamerFfmpeg(self.ytdl, self.exec_comm))
		try:
			self.ytdl.set_format(self.ui.get_selected_fmt_id_list())
			# self._streamer_list[-1].stream_start()
			self.streamer_list[-1].stream_start_detached()
		except Exception as e:
			self.ui.error_dialog_exec('Error', str(e))

	def play_file(self):
		assert self.file_for_playback is not None
		try:
			subprocess.Popen(
				[utils.Paths.get_mpv_exe(), '--force-window', '--quiet', self.file_for_playback]
			)
		except Exception as e:
			self.ui.error_dialog_exec('Error', str(e))

	def download_cancel(self):
		self.downloader.download_cancel()

	# def process_filename(self):
	# 	"""Return True if all problems are resolved."""
	# 	name, ext = self.ytdl.get_filename()
	# 	ext = '.mkv'
	# 	filename = name + ext
	# 	if os.path.isfile(filename):
	# 		do_overwrite = self.filename_collision_dialog_exec()
	# 		# Return False if user doesn't want to overwrite
	# 		if do_overwrite:
	# 			try:
	# 				os.remove(filename)
	# 				return True
	# 			except Exception as e:
	# 				self.error_dialog_exec('File error', str(e))
	# 				return False
	# 		else:
	# 			return False
	# 	else:
	# 		return True
