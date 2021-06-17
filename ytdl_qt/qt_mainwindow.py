#!/usr/bin/env python3

import logging
import pkgutil
from typing import List

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (
	QMainWindow,
	QTableWidgetItem,
	QProgressBar, QApplication
)

from ytdl_qt.history import History
from ytdl_qt.qt_historytablemodel import HistoryTableModel
from ytdl_qt.qt_mainwindow_form import Ui_MainWindow
from ytdl_qt.ytdl import Ytdl


class MainWindow(QMainWindow):

	window_title = 'ytdl-qt'
	window_icon = 'ytdl.svg'
	resources_pkg = 'resources'

	_showStatusMsg = pyqtSignal(str)
	_playButtonEnable = pyqtSignal(bool)
	_redraw = pyqtSignal()
	_progressBarMaxSet = pyqtSignal(int)
	_progressBarValSet = pyqtSignal(int)
	_alertSet = pyqtSignal()

	def __init__(self):
		super().__init__()
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		data = pkgutil.get_data(__name__, f'{self.resources_pkg}/{self.window_icon}')
		px = QPixmap()
		px.loadFromData(data)
		self.setWindowIcon(QIcon(px))
		self.setWindowTitle(self.window_title)

		self.progressBar = QProgressBar()
		self.statusBar().addPermanentWidget(self.progressBar)
		self.progressBar.setVisible(False)
		self.ui.ytdlRadio.setChecked(True)
		self.ui.urlEdit.setFocus()
		self.ui.historyView.verticalHeader().hide()

		self._showStatusMsg.connect(self._showStatusMsg_slot, type=Qt.QueuedConnection)
		self._playButtonEnable.connect(self._playButtonEnable_slot, type=Qt.QueuedConnection)
		self._redraw.connect(self._redraw_slot, type=Qt.QueuedConnection)
		self._progressBarMaxSet.connect(self._set_progressBar_max_slot, type=Qt.QueuedConnection)
		self._progressBarValSet.connect(self._set_progressBar_value_slot, type=Qt.QueuedConnection)
		self._alertSet.connect(self._set_alert_slot, type=Qt.QueuedConnection)

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

	def lock_ui(self):
		self.ui.urlEdit.setDisabled(True)
		self.ui.getInfoButton.setDisabled(True)
		self.ui.cancelButton.setEnabled(True)
		self.progressBar.setVisible(True)
		self.ui.downloadButton.setDisabled(True)
		self.ui.playButton.setDisabled(True)

	@pyqtSlot()
	def unlock_ui(self):
		self.ui.urlEdit.setEnabled(True)
		self.ui.getInfoButton.setEnabled(True)
		self.ui.cancelButton.setDisabled(True)
		self.progressBar.setVisible(False)

	def set_history(self, hist: History):
		self.ui.historyView.setModel(HistoryTableModel(hist))

	#def set_progressBar_max(self, value: int):
		#self.progressBar.setMaximum(value)

	def set_progressBar_max(self, value: int):
		self._progressBarMaxSet.emit(value)

	@pyqtSlot(int)
	def _set_progressBar_max_slot(self, value: int):
		self.progressBar.setMaximum(value)

	def set_progressBar_value(self, value: int):
		self._progressBarValSet.emit(value)

	@pyqtSlot(int)
	def _set_progressBar_value_slot(self, value: int):
		self.progressBar.setValue(value)

	def get_url(self) -> str:
		return self.ui.urlEdit.text().strip()

	def set_url(self, url: str):
		self.ui.urlEdit.setText(url)

	def lock_info(self):
		self.ui.tabWidget.setDisabled(True)

	def unlock_info(self):
		self.ui.tabWidget.setDisabled(False)

	def play_set_disabled(self):
		self.ui.playButton.setEnabled(False)

	def history_add_item(self, title: str, url: str):
		if self.ui.historyView.model() is not None:
			self.ui.historyView.model().add_history_item(title, url)

	def get_selected_formats(self):
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

	###############
	def show_status_msg(self, msg: str):
		self._showStatusMsg.emit(msg)

	@pyqtSlot(str)
	def _showStatusMsg_slot(self, msg: str):
		self.statusBar().showMessage(msg)

	def playButton_set_enabled(self, yes: bool):
		self._playButtonEnable.emit(yes)

	@pyqtSlot(bool)
	def _playButtonEnable_slot(self, yes: bool):
		self.ui.playButton.setEnabled(yes)

	def redraw(self):
		self._redraw.emit()

	@pyqtSlot()
	def _redraw_slot(self):
		QApplication.processEvents()

	def set_alert(self):
		self._alertSet.emit()

	@pyqtSlot()
	def _set_alert_slot(self):
		QApplication.alert(self, 0)

	def enable_apply_and_cancel_buttons(self):
		self.ui.applyChangesButton.setEnabled(True)
		self.ui.cancelChangesButton.setEnabled(True)

	def disable_apply_and_cancel_buttons(self):
		self.ui.applyChangesButton.setEnabled(False)
		self.ui.cancelChangesButton.setEnabled(False)







