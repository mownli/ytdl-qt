#!/usr/bin/env python3

import logging
import pkgutil
import re
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (
	QApplication,
	QMainWindow,
	QMessageBox,
	QTableWidgetItem,
	QProgressBar
)

from ytdl_qt.history import History
from ytdl_qt.qt_historytablemodel import HistoryTableModel
from ytdl_qt.qt_mainwindow_form import Ui_MainWindow
from ytdl_qt.ytdl import Ytdl


class MainWindow(QMainWindow):

	ansi_esc = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
	window_icon = 'ytdl.svg'
	resources_pkg = 'resources'

	def __init__(self):
		"""Create MainWindow."""
		super().__init__()

		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		data = pkgutil.get_data(__name__, f'{self.resources_pkg}/{self.window_icon}')
		px = QPixmap()
		px.loadFromData(data)
		self.setWindowIcon(QIcon(px))

		self.progressBar = QProgressBar()
		self.statusBar().addPermanentWidget(self.progressBar)
		self.progressBar.setVisible(False)
		self.ui.ytdlRadio.setChecked(True)
		self.ui.urlEdit.setFocus()
		self.ui.historyView.verticalHeader().hide()

		self.ui.getInfoButton.clicked.connect(self.getInfoButton_clicked_slot)
		self.ui.urlEdit.textChanged.connect(self.urlEdit_textChanged_slot)
		self.ui.infoTableWidget.itemSelectionChanged.connect(
			self.infoTableWidget_selectionChanged_slot
		)
		self.ui.downloadButton.clicked.connect(self.downloadButton_clicked_slot)
		self.ui.cancelButton.clicked.connect(self.cancelButton_clicked_slot)
		self.ui.streamButton.clicked.connect(self.streamButton_clicked_slot)
		self.ui.infoTableWidget.itemDoubleClicked.connect(self.streamButton_clicked_slot)
		self.ui.playButton.clicked.connect(self.playButton_clicked_slot)
		self.ui.historyView.doubleClicked.connect(self.history_item_clicked_slot)
		self.history_signal_connected = True

	def get_info(self, url: str):
		raise NotImplementedError

	def is_d_blocked(self) -> bool:
		raise NotImplementedError

	def download(self):
		raise NotImplementedError

	def cancelled(self):
		raise NotImplementedError

	def stream(self):
		raise NotImplementedError

	def play(self):
		raise NotImplementedError

	def set_progressBar_max(self, value: int):
		self.progressBar.setMaximum(value)

	def set_progressBar_value(self, value: int):
		self.progressBar.setValue(value)

	def update(self):
		QApplication.processEvents()

	def block_ui(self, yes=True):
		"""Block UI."""
		logging.debug(f'yes={yes}')
		self.ui.tabWidget.setDisabled(yes)

	def unblock_ui(self, yes=True):
		"""Unblock UI."""
		self.block_ui(not yes)

	def show_status_msg(self, msg: str):
		self.statusBar().showMessage(msg)

	def update_table(self, fmt_list: List[str]):
		"""Update table contents."""
		self.ui.infoTableWidget.clearContents()
		self.ui.infoTableWidget.setRowCount(len(fmt_list))
		for index, item in enumerate(fmt_list):
			self.ui.infoTableWidget.setItem(index, 0, QTableWidgetItem(item[Ytdl.Keys.id]))
			self.ui.infoTableWidget.setItem(index, 1, QTableWidgetItem(item[Ytdl.Keys.vcodec]))
			self.ui.infoTableWidget.setItem(index, 2, QTableWidgetItem(item[Ytdl.Keys.acodec]))
			self.ui.infoTableWidget.setItem(index, 3, QTableWidgetItem(item[Ytdl.Keys.dimensions]))
			self.ui.infoTableWidget.setItem(index, 4, QTableWidgetItem(item[Ytdl.Keys.size]))

	def playButton_set_disabled(self, yes=True):
		self.ui.playButton.setDisabled(yes)

	def set_window_title(self, title: str):
		self.setWindowTitle(title)

	def history_add_item(self, title: str, url: str):
		if self.ui.historyView.model() is not None:
			self.ui.historyView.model().add_history_item(title, url)

	@staticmethod
	def error_dialog_exec(status_str: str, msg: str, severity=QMessageBox.Critical):
		"""
		Throw an error dialog.
		Accepts title string, message string and QMessageBox message type.
		"""
		dialog = QMessageBox()
		dialog.setIcon(severity)
		# For cleaning ANSI stuff from exception messages
		msg_clean = MainWindow.ansi_esc.sub('', msg)
		dialog.setText(msg_clean)
		dialog.setWindowTitle(status_str)
		dialog.exec_()

	def set_playButton_enabled(self, yes=True):
		self.ui.playButton.setEnabled(yes)

	def release_ui(self):
		"""Release UI from downloaders hold."""
		logging.debug('')
		self.ui.urlEdit.setEnabled(True)
		self.ui.getInfoButton.setEnabled(True)
		self.infoTableWidget_selectionChanged_slot()
		self.ui.cancelButton.setDisabled(True)
		if not self.history_signal_connected:
			self.ui.historyView.doubleClicked.connect(self.history_item_clicked_slot)
		self.history_signal_connected = True
		self.progressBar.setVisible(False)

	def get_selected_fmt_id_list(self):
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

	# Qt slots
	# def get_info_auto_slot(self):
	# 	self.download_info(self.url_from_stdin)

	# def urlEdit_get_text(self):
	# 	return self.ui.urlEdit.text().strip()

	def urlEdit_set_text(self, text: str) -> str:
		return self.ui.urlEdit.setText(text)

	def getInfoButton_clicked_slot(self):
		url = self.ui.urlEdit.text().strip()
		self.get_info(url)

	def history_item_clicked_slot(self, index: int):
		"""Qt slot. Get URl from selected item and call self.download_info()"""
		assert self.ui.historyView.model() is not None
		url = self.ui.historyView.model().get_url(index)
		self.ui.urlEdit.setText(url)
		self.ui.tabWidget.setCurrentWidget(self.ui.mainTab)
		self.get_info(url)

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
			if not self.is_d_blocked():
				self.ui.downloadButton.setEnabled(True)
			self.ui.streamButton.setEnabled(True)
		else:
			self.ui.downloadButton.setEnabled(False)
			self.ui.streamButton.setEnabled(False)

	def setup_ui_for_download(self):
		self.ui.urlEdit.setDisabled(True)
		self.ui.getInfoButton.setDisabled(True)
		self.ui.downloadButton.setDisabled(True)
		self.ui.getInfoButton.setDisabled(True)
		self.ui.cancelButton.setEnabled(True)
		self.ui.playButton.setDisabled(True)
		if self.history_signal_connected:
			self.ui.historyView.doubleClicked.disconnect(self.history_item_clicked_slot)
			self.history_signal_connected = False
		self.progressBar.setVisible(True)

	def downloadButton_clicked_slot(self):
		"""Qt slot. Run selected downloader."""
		logging.debug('')
		self.download()

	def cancelButton_clicked_slot(self):
		"""Qt slot. Send cancel signal to running downloader."""
		logging.debug('')
		self.cancelled()

	def streamButton_clicked_slot(self):
		"""Qt slot. Use FFmpeg downloader to stream selected items."""
		logging.debug('')
		self.stream()

	def playButton_clicked_slot(self):
		"""Qt slot. Start playback of the last downloaded file."""
		logging.debug('')
		self.play()

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

	def is_ytdl_checked(self) -> bool:
		return self.ui.ytdlRadio.isChecked()

	def is_ffmpeg_checked(self) -> bool:
		return self.ui.ffmpegRadio.isChecked()

	def is_aria2_checked(self) -> bool:
		return self.ui.aria2Radio.isChecked()

	def set_history(self, hist: History):
		self.ui.historyView.setModel(HistoryTableModel(hist))

	def set_alert(self):
		QApplication.alert(self, 0)
