#!/usr/bin/env python3

import logging
import os
import re
import subprocess

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
	QApplication,
	QMainWindow,
	QMessageBox,
	QTableWidgetItem,
	QProgressBar
)

from ytdl_qt.downloader_aria2c import DownloaderAria2c
from ytdl_qt.downloader_ffmpeg import DownloaderFfmpeg
from ytdl_qt.downloader_ytdl import DownloaderYtdl
from ytdl_qt.qt_historytablemodel import HistoryTableModel
from ytdl_qt.qt_mainwindow_form import Ui_MainWindow
from ytdl_qt.ytdl import Ytdl
from ytdl_qt import utils


class MainWindow(QMainWindow):

	WINDOW_TITLE = 'ytdl-qt'
	ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

	def __init__(self, url=None):
		"""Create MainWindow."""
		super().__init__()

		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		self.ytdl = Ytdl()

		self._progressBar = QProgressBar()
		self.statusBar().addPermanentWidget(self._progressBar)
		self._progressBar.setVisible(False)
		self.ui.ytdlRadio.setChecked(True)
		self.ui.urlEdit.setFocus()
		self.setWindowTitle(self.WINDOW_TITLE)

		self.ui.getInfoButton.clicked.connect(self.getInfoButton_clicked_slot)
		self.ui.urlEdit.textChanged.connect(self.urlEdit_textChanged_slot)
		self.ui.infoTableWidget.itemSelectionChanged.connect(
			self.infoTableWidget_selectionChanged_slot
		)
		self.ui.downloadButton.clicked.connect(self.downloadButton_clicked_slot)
		self.ui.cancelButton.clicked.connect(self.cancelButton_clicked_slot)
		self.ui.streamButton.clicked.connect(self.streamButton_clicked_slot)
		self.ui.playButton.clicked.connect(self.playButton_clicked_slot)
		self.ui.historyView.doubleClicked.connect(self.history_item_clicked_slot)
		self.history_signal_connected = True
		self._ui_blocked = False
		self._download_blocked = False
		self._file_for_playback = None

		self._downloader = None
		self._streamer_list = []

		try:
			self._load_history(utils.Paths.get_history())
		except Exception as e:
			logging.debug("Failed to load history")
			raise e
			pass

		self.ui.historyView.verticalHeader().hide()

		if url is not None:
			# Slot is called after the window is shown
			QTimer.singleShot(0, self.get_info_auto_slot)
			self.url_from_stdin = url.strip()
			self.ui.urlEdit.setText(self.url_from_stdin)

	def _download_info(self, url):
		"""
		Download URL info, update tableWidget and history, reset playback
		information on success. Blocks UI.
		"""
		logging.debug(f"Loading info for {url}")
		assert url is not None
		self._block_ui()
		self.statusBar().showMessage('Downloading info')
		QApplication.processEvents()

		try:
			self.ytdl.download_info(url)

			self._update_table()
			self._file_for_playback = None
			self.ui.playButton.setDisabled(True)
			self.setWindowTitle(self.WINDOW_TITLE + ' :: ' + self.ytdl.get_title())
			self.statusBar().showMessage('Info loaded')

			# Add item to history
			if self.ui.historyView.model() is not None:
				self.ui.historyView.model().add_history_item(self.ytdl.get_title(), url)
		except Exception as e:
			self.error_dialog_exec('Info loading error', str(e))
			self.statusBar().showMessage('Info loading error')

		self._unblock_ui()

	def set_playback_enabled(self, path):
		"""Enable playButton for file playback."""
		logging.debug('')
		assert path is not None
		self._file_for_playback = path
		self.ui.playButton.setEnabled(True)

	# UI stuff
	def _block_ui(self, yes=True):
		"""Block UI."""
		logging.debug(f'yes={yes}')
		self.ui.tabWidget.setDisabled(yes)

	def _unblock_ui(self, yes=True):
		"""Unblock UI."""
		self._block_ui(not yes)

	def release_ui(self):
		"""Release UI from downloaders hold."""
		logging.debug('')
		self.ui.urlEdit.setEnabled(True)
		self.ui.getInfoButton.setEnabled(True)
		self._download_blocked = False
		self.infoTableWidget_selectionChanged_slot()
		self.ui.cancelButton.setDisabled(True)
		if not self.history_signal_connected:
			self.ui.historyView.doubleClicked.connect(self.history_item_clicked_slot)
		self.history_signal_connected = True
		self.setWindowTitle(self.WINDOW_TITLE + ' :: ' + self.ytdl.get_title())
		self._progressBar.setVisible(False)

	def _update_table(self):
		"""Update table contents."""
		fmt_list = self.ytdl.get_info()
		self.ui.infoTableWidget.clearContents()
		self.ui.infoTableWidget.setRowCount(len(fmt_list))
		for index, item in enumerate(fmt_list):
			self.ui.infoTableWidget.setItem(index, 0, QTableWidgetItem(item[self.ytdl.Keys.id]))
			self.ui.infoTableWidget.setItem(index, 1, QTableWidgetItem(item[self.ytdl.Keys.vcodec]))
			self.ui.infoTableWidget.setItem(index, 2, QTableWidgetItem(item[self.ytdl.Keys.acodec]))
			self.ui.infoTableWidget.setItem(index, 3, QTableWidgetItem(item[self.ytdl.Keys.dimensions]))
			self.ui.infoTableWidget.setItem(index, 4, QTableWidgetItem(item[self.ytdl.Keys.size]))

	def _get_selected_fmt_id_list(self):
		"""Return list of selected format ids from the table."""
		fmt_set = set()
		for i in self.ui.infoTableWidget.selectedItems():
			fmt_id = self.ui.infoTableWidget.item(i.row(), 0).data(Qt.DisplayRole)
			if fmt_id is not None:
				fmt_set.add(fmt_id)
		# fmt_id = self.ui.infoTableWidget.item(i.row(), 0).text()
		# if fmt_id != '':
		# 	fmt_set.add(fmt_id)

		logging.debug(f"Selected formats {fmt_set}")
		return list(fmt_set)

	def _load_history(self, path):
		"""Try to load history from path."""
		logging.debug('Trying to load history')

		history_model = HistoryTableModel(path)
		self.ui.historyView.setModel(history_model)
		logging.debug('History loaded')

	# Qt slots
	def get_info_auto_slot(self):
		self._download_info(self.url_from_stdin)

	def getInfoButton_clicked_slot(self):
		url = self.ui.urlEdit.text().strip()
		self._download_info(url)

	def history_item_clicked_slot(self, index):
		"""Qt slot. Get URl from selected item and call self._download_info()"""
		assert self.ui.historyView.model() is not None
		url = self.ui.historyView.model().get_url(index)
		self.ui.urlEdit.setText(url)
		self.ui.tabWidget.setCurrentWidget(self.ui.mainTab)
		self._download_info(url)

	def urlEdit_textChanged_slot(self):
		"""Qt slot. Enable getInfoButton if urlEdit is not empty."""
		if not self.ui.urlEdit.text():
			self.ui.getInfoButton.setEnabled(False)
		else:
			self.ui.getInfoButton.setEnabled(True)

	def infoTableWidget_selectionChanged_slot(self):
		"""
		Qt slot. Enable streamButton and downloadButton if
		there are selected items in the tableWidget.
		"""
		if self.ui.infoTableWidget.selectedItems():
			if not self._download_blocked:
				self.ui.downloadButton.setEnabled(True)
			self.ui.streamButton.setEnabled(True)
		else:
			self.ui.downloadButton.setEnabled(False)
			self.ui.streamButton.setEnabled(False)

		if self.ytdl.get_info() is not None:
			logging.debug(
				f"Selection {self.ytdl.get_url_list_by_ids(self._get_selected_fmt_id_list())}"
			)

	def downloadButton_clicked_slot(self):
		"""Qt slot. Run selected downloader."""
		# if not self.process_filename():
		# 	return

		if self.ui.ytdlRadio.isChecked():
			self._downloader = DownloaderYtdl(self.ytdl)
		elif self.ui.ffmpegRadio.isChecked():
			self._downloader = DownloaderFfmpeg(self.ytdl)
		elif self.ui.aria2Radio.isChecked():
			self._downloader = DownloaderAria2c(self.ytdl)

		self._downloader.com.set_pbar_max_signal.connect(self._progressBar.setMaximum)
		self._downloader.com.set_pbar_value_signal.connect(self._progressBar.setValue)
		self._downloader.com.show_msg_signal.connect(self.statusBar().showMessage)
		self._downloader.com.release_signal.connect(self.release_ui)
		self._downloader.com.ready_for_playback_signal.connect(self.set_playback_enabled)

		try:
			self.ytdl.set_format(self._get_selected_fmt_id_list())

			self.ui.urlEdit.setDisabled(True)
			self.ui.getInfoButton.setDisabled(True)
			self._download_blocked = True
			self.ui.downloadButton.setDisabled(True)
			self.ui.getInfoButton.setDisabled(True)
			self.ui.cancelButton.setEnabled(True)
			self.ui.playButton.setDisabled(True)
			if self.history_signal_connected:
				self.ui.historyView.doubleClicked.disconnect(self.history_item_clicked_slot)
				self.history_signal_connected = False
			self.setWindowTitle(
				self.WINDOW_TITLE + ' :: Downloading :: ' + self.ytdl.get_title()
			)
			self._progressBar.setVisible(True)

			self._downloader.download_start()
		except Exception as e:
			self.error_dialog_exec('Download Error', str(e))

	def cancelButton_clicked_slot(self):
		"""Qt slot. Send cancel signal to running downloader."""
		logging.debug('')
		self._downloader.download_cancel()

	def streamButton_clicked_slot(self):
		"""Qt slot. Use FFmpeg downloader to stream selected items."""
		self._streamer_list.append(DownloaderFfmpeg(self.ytdl))
		try:
			self.ytdl.set_format(self._get_selected_fmt_id_list())
			# self._streamer_list[-1].stream_start()
			self._streamer_list[-1].stream_start_detached()
		except Exception as e:
			self.error_dialog_exec('Error', str(e))

	def playButton_clicked_slot(self):
		"""Qt slot. Start playback of the last downloaded file."""
		assert self._file_for_playback is not None
		try:
			subprocess.Popen(
				[utils.Paths.get_mpv_exe(), '--force-window', '--quiet', self._file_for_playback]
			)
		except Exception as e:
			self.error_dialog_exec('Error', str(e))

	# Helpers
	@staticmethod
	def error_dialog_exec(status_str, msg, severity=QMessageBox.Critical):
		"""
		Throw an error dialog.
		Accepts title string, message string and QMessageBox message type.
		"""
		dialog = QMessageBox()
		dialog.setIcon(severity)
		# For cleaning ANSI stuff from exception messages
		msg_clean = MainWindow.ANSI_ESCAPE.sub('', msg)
		dialog.setText(msg_clean)
		dialog.setWindowTitle(status_str)
		dialog.exec_()

	@staticmethod
	def filename_collision_dialog_exec():
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

	def process_filename(self):
		"""Return True if all problems are resolved."""
		name, ext = self.ytdl.get_filename()
		ext = '.mkv'
		filename = name + ext
		if os.path.isfile(filename):
			do_overwrite = self.filename_collision_dialog_exec()
			# Return False if user doesn't want to overwrite
			if do_overwrite:
				try:
					os.remove(filename)
					return True
				except Exception as e:
					self.error_dialog_exec('File error', str(e))
					return False
			else:
				return False
		else:
			return True
