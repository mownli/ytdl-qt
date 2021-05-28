#!/usr/bin/env python3

import logging
import re

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
	QApplication,
	QMessageBox,
)

import ytdl_qt.utils as utils
from ytdl_qt.qt_mainwindow import MainWindow
from ytdl_qt.core import Core, Callbacks
from ytdl_qt.history import History


class QtWrapper:

	# For clearing ANSI stuff from exception messages
	ansi_esc = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

	def __init__(self):
		self.app = QApplication([])

		self.w: MainWindow = MainWindow()
		self.history_widget_connected = False
		self.connect_mainwindow_signals(self.w)
		self.w.show()

		self.core = Core()
		self.set_core_callbacks(self.core)

		self.url_from_stdin = None
		self.load_history()

	def connect_mainwindow_signals(self, mw: MainWindow):
		mw.ui.getInfoButton.clicked.connect(self.getInfoButton_clicked_slot)
		mw.ui.urlEdit.textChanged.connect(self.urlEdit_textChanged_slot)
		mw.ui.downloadButton.clicked.connect(self.downloadButton_clicked_slot)
		mw.ui.cancelButton.clicked.connect(self.cancelButton_clicked_slot)
		mw.ui.streamButton.clicked.connect(self.streamButton_clicked_slot)
		mw.ui.infoTableWidget.itemDoubleClicked.connect(self.streamButton_clicked_slot)
		mw.ui.playButton.clicked.connect(self.playButton_clicked_slot)
		mw.ui.infoTableWidget.itemSelectionChanged.connect(
			self.infoTableWidget_selectionChanged_slot
		)
		self.connect_history_widget()

	def set_core_callbacks(self, core: Callbacks):
		core.task_finished_cb = self.task_finish
		core.playback_enabled_cb = self.w.play_set_enabled
		core.redraw_cb = self.app.processEvents
		core.set_progress_max_cb = self.w.set_progressBar_max
		core.set_progress_val_cb = self.w.set_progressBar_value
		core.show_msg_cb = self.show_status_msg

	def load_history(self):
		logging.debug('Trying to load history')
		hist = History(utils.Paths.get_history())
		self.w.set_history(hist)
		logging.debug('History loaded')

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
			self.w.set_window_title(self.w.window_title + ' :: ' + self.core.get_title())
			self.show_status_msg('Info loaded')

			self.w.history_add_item(self.core.get_title(), url)
		except Exception as e:
			self.error_dialog_exec('Info loading error', str(e))
			self.show_status_msg('Info loading error')

		self.w.unlock_info()

	def task_finish(self, signal: tuple[bool, str]):
		success, error_str = signal
		if not success:
			self.error_dialog_exec('Error', error_str)

		self.set_alert()
		self.w.set_window_title(self.w.window_title + ' :: ' + self.core.get_title())
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
		self.app.processEvents()

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
		self.w.set_window_title(
			self.w.window_title + ' :: Downloading :: ' + self.core.get_title()
		)
		self.disconnect_history_widget()
		self.w.lock_ui()

	def unlock_ui(self):
		"""Release UI from downloaders hold."""
		self.infoTableWidget_selectionChanged_slot()
		self.w.unlock_ui()
		self.connect_history_widget()

	def get_info_auto_slot(self):
		"""Qt slot. For a timer during instantiation."""
		self.download_info(self.url_from_stdin)

	def getInfoButton_clicked_slot(self):
		"""Qt slot."""
		self.download_info(self.w.get_url())

	def history_item_clicked_slot(self, index: int):
		"""Qt slot. Get URl from selected item and reload info."""
		assert self.w.ui.historyView.model() is not None
		url = self.w.ui.historyView.model().get_url(index)
		self.w.set_url(url)
		self.w.ui.tabWidget.setCurrentWidget(self.w.ui.mainTab)
		self.download_info(url)

	def urlEdit_textChanged_slot(self):
		"""Qt slot. Enable getInfoButton if urlEdit is not empty."""
		if not self.w.ui.urlEdit.text():
			self.w.ui.getInfoButton.setEnabled(False)
		else:
			self.w.ui.getInfoButton.setEnabled(True)

	def infoTableWidget_selectionChanged_slot(self):
		"""
		Qt slot. Enable streamButton and downloadButton if
		there are selected items in the tableWidget.
		"""
		if self.w.ui.infoTableWidget.selectedItems():
			if not self.core.is_download_blocked():
				self.w.ui.downloadButton.setEnabled(True)
			self.w.ui.streamButton.setEnabled(True)
		else:
			self.w.ui.downloadButton.setEnabled(False)
			self.w.ui.streamButton.setEnabled(False)

	def downloadButton_clicked_slot(self):
		"""Qt slot. Get selected formats and run selected downloader."""
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
		"""Qt slot. Send cancel signal to running downloader."""
		self.core.download_cancel()

	def streamButton_clicked_slot(self):
		"""Qt slot. Use FFmpeg downloader to stream selected items."""
		try:
			formats = self.w.get_selected_formats()
			logging.debug(f'Selected formats {formats}')
			self.core.set_format(formats)
			self.core.stream_target()
		except Exception as e:
			self.error_dialog_exec('Download Error', str(e))

	def playButton_clicked_slot(self):
		"""Qt slot. Start playback of the last downloaded file."""
		try:
			self.core.play_target()
		except Exception as e:
			self.error_dialog_exec('Error', str(e))

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
