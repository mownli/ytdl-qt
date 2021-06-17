#!/usr/bin/env python3

import logging
import re
import shlex
from typing import Tuple

from PyQt5.QtCore import QTimer, pyqtSlot, QMetaObject, Qt, Q_RETURN_ARG
from PyQt5.QtWidgets import (
	QApplication,
	QMessageBox, QFileDialog
)

from ytdl_qt.paths import Paths
from ytdl_qt.qt_mainwindow import MainWindow
from ytdl_qt.core import Core, Callbacks
from ytdl_qt.history import History
from ytdl_qt.settings import Settings


class QtWrapper:

	# For clearing ANSI stuff from exception messages
	ansi_esc = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

	def __init__(self):
		self.app = QApplication([])
		self.w: MainWindow = MainWindow()

		self.core = Core()
		self.set_core_callbacks(self.core)

		self.settings = Settings()

		if not self.settings.ffmpeg_path.current:
			self.msg_box = QMessageBox(self.w)
			self.msg_box.setIcon(QMessageBox.Warning)
			self.msg_box.setText('Couldn\'t locate FFmpeg binary. Set the path in the settings tab')

			def delete_box():
				del self.msg_box

			self.msg_box.finished.connect(delete_box)
			self.msg_box.open()

		self.w.ui.ffmpegPathEdit.setText(self.settings.ffmpeg_path.current)
		self.w.ui.playerPathEdit.setText(self.settings.player_path.current)
		self.w.ui.playerParamsEdit.setText(self.settings.player_params.current)
		self.set_settings_core()
		self.set_settings_ui()

		self.history_widget_connected = False
		self.connect_signals()

		logging.debug('Trying to load history')
		self.w.set_history(History(Paths.get_history_path()))
		logging.debug('History loaded')

		self.url_from_stdin = None
		self.w.show()

	################################ Settings stuff
	def set_settings_core(self):
		self.core.set_ffmpeg_path(self.settings.ffmpeg_path.current)
		self.core.set_player_path(self.settings.player_path.current)
		self.core.set_player_params(shlex.split(self.settings.player_params.current))

	def set_settings_ui(self):
		if self.settings.ffmpeg_path.current:
			self.w.ui.ffmpegPathEdit.setText(self.settings.ffmpeg_path.current)
		self.w.ui.ffmpegRadio.setEnabled(bool(self.settings.ffmpeg_path.current))

	def commit_settings(self):
		try:
			self.settings.ffmpeg_path.set(self.w.ui.ffmpegPathEdit.text().strip())
			self.settings.player_path.set(self.w.ui.playerPathEdit.text().strip())
			self.settings.player_params.set(self.w.ui.playerParamsEdit.text().strip())
		except Exception as e:
			self.error_dialog_exec('FFmpeg', str(e))
			return
		self.settings.save()

		self.set_settings_core()
		self.set_settings_ui()
		self.w.disable_apply_and_cancel_buttons()

	def undo_settings(self):
		self.w.ui.ffmpegPathEdit.setText(self.settings.ffmpeg_path.current)
		self.w.ui.playerPathEdit.setText(self.settings.player_path.current)
		self.w.ui.playerParamsEdit.setText(self.settings.player_params.current)

		self.w.disable_apply_and_cancel_buttons()

	def pick_exe_ffmpeg(self):
		path = self.filepicker()
		if path:
			self.w.ui.ffmpegPathEdit.setText(path)
			self.w.enable_apply_and_cancel_buttons()

	def pick_exe_player(self):
		path = self.filepicker()
		if path:
			self.w.ui.playerPathEdit.setText(path)
			self.w.enable_apply_and_cancel_buttons()

	def filepicker(self):
		d = QFileDialog(caption='Provide path to the executable')
		if d.exec_():
			path = d.selectedFiles()[0]
			return path
		else:
			return None
	########################################

	def connect_signals(self):
		self.w.ui.getInfoButton.clicked.connect(self.getInfoButton_clicked_slot)
		self.w.ui.urlEdit.textChanged.connect(self.urlEdit_textChanged_slot)
		self.w.ui.downloadButton.clicked.connect(self.downloadButton_clicked_slot)
		self.w.ui.cancelButton.clicked.connect(self.cancelButton_clicked_slot)
		self.w.ui.streamButton.clicked.connect(self.streamButton_clicked_slot)
		self.w.ui.infoTableWidget.itemDoubleClicked.connect(self.streamButton_clicked_slot)
		self.w.ui.playButton.clicked.connect(self.playButton_clicked_slot)
		self.w.ui.infoTableWidget.itemSelectionChanged.connect(
			self.infoTableWidget_selectionChanged_slot
		)

		self.connect_history_widget()

		self.w.ui.ffmpegPathEdit.textEdited.connect(self.w.enable_apply_and_cancel_buttons)
		self.w.ui.playerPathEdit.textEdited.connect(self.w.enable_apply_and_cancel_buttons)
		self.w.ui.playerParamsEdit.textEdited.connect(self.w.enable_apply_and_cancel_buttons)

		self.w.ui.ffmpegPathButton.clicked.connect(self.pick_exe_ffmpeg)
		self.w.ui.playerPathButton.clicked.connect(self.pick_exe_player)

		self.w.ui.applyChangesButton.clicked.connect(self.commit_settings)
		self.w.ui.cancelChangesButton.clicked.connect(self.undo_settings)

	def set_core_callbacks(self, core: Callbacks):
		core.task_finished_cb = self.task_finish
		core.playback_enabled_cb = self.play_set_enabled
		#core.redraw_cb = self.app.processEvents
		core.redraw_cb = self.w.redraw
		core.set_progress_max_cb = self.w.set_progressBar_max
		core.set_progress_val_cb = self.w.set_progressBar_value
		core.show_msg_cb = self.show_status_msg

	def download_info(self, url: str):
		"""
		Download URL info, update tableWidget and history, reset playback
		information on success. Blocks UI.
		"""
		logging.debug(f"Loading info for {url}")
		self.w.lock_info()
		self.show_status_msg('Downloading info')

		try:
			self.core.download_info(url)

			self.w.update_table(self.core.get_info())
			self.w.play_set_disabled()
			self.w.setWindowTitle(self.w.window_title + ' :: ' + self.core.get_title())
			self.show_status_msg('Info loaded')

			self.w.history_add_item(self.core.get_title(), url)
		except Exception as e:
			self.error_dialog_exec('Info loading error', str(e))
			self.show_status_msg('Info loading error')

		self.w.unlock_info()

	def task_finish(self, signal: Tuple[bool, str]):
		success, error_str = signal
		if not success:
			self.error_dialog_exec('Error', error_str)

		#self.set_alert()
		self.w.set_alert()
		self.w.setWindowTitle(self.w.window_title + ' :: ' + self.core.get_title())
		self.unlock_ui()

	def disconnect_history_widget(self):
		if self.history_widget_connected:
			self.w.ui.historyView.doubleClicked.disconnect(self.history_item_clicked_slot)
			self.history_widget_connected = False

	def connect_history_widget(self):
		if not self.history_widget_connected:
			self.w.ui.historyView.doubleClicked.connect(self.history_item_clicked_slot)
			self.history_widget_connected = True

	def show_status_msg(self, msg: str):
		self.w.show_status_msg(msg)
		#self.app.processEvents()

	def set_alert(self):
		self.app.alert(self.w, 0)

	def exec(self, url=None) -> int:
		if url is not None:
			# Slot is called after the window is shown
			QTimer.singleShot(0, self.get_info_auto_slot)
			self.url_from_stdin = url
			self.w.set_url(self.url_from_stdin)
		# if url is not None:
		# 	self.w.set_url(url)
		# 	self.core.download_info(url)
		return self.app.exec_()

	def lock_ui_for_download(self):
		self.w.setWindowTitle(
			self.w.window_title + ' :: Downloading :: ' + self.core.get_title()
		)
		self.disconnect_history_widget()
		self.w.lock_ui()

	def unlock_ui(self):
		"""Release UI from downloaders hold."""
		self.infoTableWidget_selectionChanged_slot()

		self.w.metaObject().invokeMethod(self.w, self.w.unlock_ui.__name__, Qt.QueuedConnection)

		#self.w.unlock_ui()

		self.connect_history_widget()

	#@pyqtSlot()
	def get_info_auto_slot(self):
		"""For a timer during instantiation."""
		self.download_info(self.url_from_stdin)

	def getInfoButton_clicked_slot(self):
		self.download_info(self.w.get_url())

	def history_item_clicked_slot(self, index: int):
		"""Get URl from selected item and reload info."""
		assert self.w.ui.historyView.model() is not None
		url = self.w.ui.historyView.model().get_url(index)
		self.w.set_url(url)
		self.w.ui.tabWidget.setCurrentWidget(self.w.ui.mainTab)
		self.download_info(url)

	def urlEdit_textChanged_slot(self):
		"""Enable getInfoButton if urlEdit is not empty."""
		if not self.w.ui.urlEdit.text().strip():
			self.w.ui.getInfoButton.setEnabled(False)
		else:
			self.w.ui.getInfoButton.setEnabled(True)

	def infoTableWidget_selectionChanged_slot(self):
		"""
		Enable streamButton and downloadButton if
		there are selected items in the tableWidget.
		"""
		if self.w.ui.infoTableWidget.selectedItems():
			if not self.core.is_download_blocked():
				self.w.ui.downloadButton.setEnabled(True)
			can_stream = bool(self.settings.ffmpeg_path.current) and bool(self.settings.player_path.current)
			self.w.ui.streamButton.setEnabled(can_stream)
		else:
			self.w.ui.downloadButton.setEnabled(False)
			self.w.ui.streamButton.setEnabled(False)

	def downloadButton_clicked_slot(self):
		"""Get selected formats and run selected downloader."""
		try:
			formats = self.w.get_selected_formats()
			logging.debug(f'Selected formats {formats}')
			self.core.set_format(formats)
			self.lock_ui_for_download()
			if self.w.ui.ytdlRadio.isChecked():
				self.core.download_with_ytdl()
			elif self.w.ui.ffmpegRadio.isChecked():
				self.core.download_with_ffmpeg()
			elif self.w.ui.aria2Radio.isChecked():
				self.core.download_with_aria2()
		except Exception as e:
			self.error_dialog_exec('Download Error', str(e))
			self.unlock_ui()

	def cancelButton_clicked_slot(self):
		"""Send cancel signal to running downloader."""
		self.core.download_cancel()

	def streamButton_clicked_slot(self):
		"""Use FFmpeg downloader to stream selected items."""
		can_stream = bool(self.settings.ffmpeg_path.current) and bool(self.settings.player_path.current)
		if not can_stream:
			self.error_dialog_exec('Stream Error', 'Provide FFmpeg and player executables')
			return
		try:
			formats = self.w.get_selected_formats()
			logging.debug(f'Selected formats {formats}')
			self.core.set_format(formats)
			self.core.stream_target()
		except Exception as e:
			self.error_dialog_exec('Stream Error', str(e))

	def playButton_clicked_slot(self):
		"""Start playback of the last downloaded file."""
		try:
			self.core.play_target()
		except Exception as e:
			self.error_dialog_exec('Error', str(e))

	def play_set_enabled(self):
		#self.w.ui.playButton.setEnabled(bool(self.settings.player_path.current))
		self.w.playButton_set_enabled(bool(self.settings.player_path.current))

	@staticmethod
	def error_dialog_exec(status_str: str, msg: str):
		"""
		Throw an error dialog.
		Accepts title string, message string and QMessageBox message type.
		"""
		severity = QMessageBox.Critical
		dialog = QMessageBox()
		dialog.setIcon(severity)
		# For cleaning ANSI stuff from exception messages
		msg_clean = QtWrapper.ansi_esc.sub('', msg)
		dialog.setText(msg_clean)
		dialog.setWindowTitle(status_str)
		dialog.exec_()

	@staticmethod
	def filename_collision_dialog_exec() -> bool:
		"""Return True if overwrite is chosen."""
		dialog = QMessageBox()
		dialog.setIcon(QMessageBox.Warning)
		dialog.setText('File with that name already exists. Overwrite?')
		dialog.setWindowTitle('Filename collision')
		dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
		dialog.setDefaultButton(QMessageBox.Yes)
		ret = dialog.exec_()
		if ret == QMessageBox.Yes:
			return True
		else:
			return False
