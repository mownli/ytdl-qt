#!/usr/bin/env python3

import logging
import subprocess

from ytdl_qt.executor_abstract import ExecutorAbstract
from ytdl_qt.streamer_abstract import StreamerAbstract
from ytdl_qt.downloader_abstract import DownloaderAbstract
from ytdl_qt.executors.streamer_ffmpeg import StreamerFfmpeg
from ytdl_qt.executors.downloader_aria2c import DownloaderAria2c
from ytdl_qt.executors.downloader_ffmpeg import DownloaderFfmpeg
from ytdl_qt.executors.downloader_ytdl import DownloaderYtdl
from ytdl_qt.ytdl import Ytdl
from ytdl_qt.qt_mainwindow import MainWindow
from ytdl_qt import utils
from ytdl_qt.history import History


class Core:

	window_title = 'ytdl-qt'

	def __init__(self, url):

		self.ytdl: Ytdl = Ytdl()
		self.downloader = None
		self.streamer_list = []

		self.ui: MainWindow = self.make_qt_ui()
		self.ui.show()
		self.load_history()

		self.d_blocked = False
		self.file_for_playback: str = ''

		if url is not None:
			self.ui.urlEdit_set_text(url)
			self.download_info(url)

		# if url is not None:
			# 	# Slot is called after the window is shown
			# 	QTimer.singleShot(0, self.get_info_auto_slot)
			# 	self.url_from_stdin = url
			# 	self.ui.urlEdit_set_text(self.url_from_stdin)

	def make_qt_ui(self) -> MainWindow:
		mw = MainWindow()
		mw.get_info = self.download_info
		mw.is_d_blocked = self.is_d_blocked
		mw.download = self.download_target
		mw.cancelled = self.download_cancel
		mw.stream = self.stream_target
		mw.play = self.play_file
		mw.set_window_title(self.window_title)
		return mw

	def download_info(self, url: str):
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

			self.file_for_playback = ''
			self.ui.update_table(self.ytdl.get_info())
			self.ui.playButton_set_disabled()
			self.ui.set_window_title(self.window_title + ' :: ' + self.ytdl.get_title())
			self.ui.show_status_msg('Info loaded')

			self.ui.history_add_item(self.ytdl.get_title(), url)
		except Exception as e:
			self.ui.error_dialog_exec('Info loading error', str(e))
			self.ui.show_status_msg('Info loading error')

		self.ui.unblock_ui()

	def set_playback_enabled(self, path: str):
		"""Enable playButton for file playback."""
		logging.debug(f'Filepath = {path}')
		assert path is not None
		self.file_for_playback = path
		self.ui.set_playButton_enabled(True)

	def release_ui(self):
		self.d_blocked = False
		self.ui.set_window_title(self.window_title + ' :: ' + self.ytdl.get_title())
		self.ui.release_ui()

	def load_history(self):
		"""Try to load history from path."""
		logging.debug('Trying to load history')
		hist = History(utils.Paths.get_history())
		self.ui.set_history(hist)
		logging.debug('History loaded')

	# def get_info_auto_slot(self):
	# 	self.download_info(self.url_from_stdin)

	def is_d_blocked(self) -> bool:
		return self.d_blocked

	def download_target(self):
		"""Run selected downloader."""
		# if not self.process_filename():
		# 	return

		if self.ui.is_ytdl_checked():
			self.downloader = DownloaderYtdl(self.ytdl)
		elif self.ui.is_ffmpeg_checked():
			self.downloader = DownloaderFfmpeg(self.ytdl)
		elif self.ui.is_aria2_checked():
			self.downloader = DownloaderAria2c(self.ytdl)

		self.connect_downloader(self.downloader)

		try:
			self.ytdl.set_format(self.ui.get_selected_fmt_id_list())
		except Exception as e:
			self.ui.error_dialog_exec('Download Error', str(e))

		self.d_blocked = True
		self.ui.setup_ui_for_download()
		self.ui.set_window_title(
			self.window_title + ' :: Downloading :: ' + self.ytdl.get_title()
		)
		self.downloader.download_start()

	def stream_target(self):
		self.streamer_list.append(StreamerFfmpeg(self.ytdl))
		self.connect_streamer(self.streamer_list[-1])
		try:
			self.ytdl.set_format(self.ui.get_selected_fmt_id_list())
		except Exception as e:
			self.ui.error_dialog_exec('Download Error', str(e))
		# self.streamer_list[-1].stream_start()
		self.streamer_list[-1].stream_start_detached()

	def play_file(self):
		assert self.file_for_playback
		try:
			subprocess.Popen(
				[utils.Paths.get_mpv_exe(), '--force-window', '--quiet', self.file_for_playback]
			)
		except Exception as e:
			self.ui.error_dialog_exec('Error', str(e))

	def download_cancel(self):
		self.downloader.download_cancel()

	def connect_downloader(self, downloader: DownloaderAbstract):
		downloader.set_pbar_max = self.ui.set_progressBar_max
		downloader.set_pbar_value = self.ui.set_progressBar_value
		downloader.show_msg = self.ui.show_status_msg
		downloader.finished = self.task_finished
		downloader.file_ready_for_playback = self.set_playback_enabled

	def connect_streamer(self, downloader: StreamerAbstract):
		downloader.set_pbar_max = self.ui.set_progressBar_max
		downloader.show_msg = self.ui.show_status_msg
		downloader.finished = self.task_finished

	def task_finished(self, sender: ExecutorAbstract):
		assert sender is not None
		self.release_ui()
		if sender.error:
			self.ui.error_dialog_exec('Error', sender.error)
			return

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
