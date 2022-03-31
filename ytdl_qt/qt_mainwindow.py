#!/usr/bin/env python3

import logging
import os
import pkgutil
import re
import shlex
from typing import List, Tuple

from PyQt5.QtCore import Qt, pyqtSlot, Q_ARG, QModelIndex
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (
	QMainWindow,
	QTableWidgetItem,
	QProgressBar,
	QApplication,
	QMessageBox,
	QFileDialog
)

from ytdl_qt.history import History
from ytdl_qt.qt_historytablemodel import HistoryTableModel
from ytdl_qt.qt_mainwindow_form import Ui_MainWindow
from ytdl_qt.ytdl_info import Info
from ytdl_qt.paths import Paths
from ytdl_qt.core import Core, Callbacks
from ytdl_qt.settings import Settings


class MainWindow(QMainWindow):

	window_title = 'ytdl-qt'
	window_icon = 'ytdl.svg'
	resources_pkg = 'resources'

	# For clearing ANSI stuff from exception messages
	ansi_esc = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

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

		self.core = Core()
		self.set_core_callbacks(self.core)

		self.settings = Settings()

		# if not self.settings.ffmpeg_path.current:
		# 	self.msg_box = QMessageBox(self)
		# 	self.msg_box.setIcon(QMessageBox.Warning)
		# 	self.msg_box.setText('Couldn\'t locate FFmpeg binary. Set the path in the settings tab')
		#
		# 	def delete_box():
		# 		del self.msg_box
		#
		# 	self.msg_box.finished.connect(delete_box)
		# 	self.msg_box.open()

		self.ui.ffmpegPathEdit.setText(self.settings.ffmpeg_path.current)
		self.ui.downloadDirEdit.setText(self.settings.download_dir.current)
		self.ui.playerPathEdit.setText(self.settings.player_path.current)
		self.ui.playerParamsEdit.setText(self.settings.player_params.current)
		self.set_settings_core()
		self.set_settings_ui()

		self.history_widget_connected = False
		self.connect_signals()

		logging.debug('Trying to load history')
		self.ui.historyView.setModel(HistoryTableModel(History(Paths.get_history_path())))
		logging.debug('History loaded')

		self.download_button_text = self.ui.downloadButton.text()
		self.download_button_status = True

	def update_table(self, fmt_list: List[str]):
		"""Update table contents."""
		self.ui.infoTableWidget.clearContents()
		self.ui.infoTableWidget.setRowCount(len(fmt_list))
		for index, item in enumerate(fmt_list):
			self.ui.infoTableWidget.setItem(index, 0, QTableWidgetItem(item[Info.Keys.id]))
			self.ui.infoTableWidget.setItem(index, 1, QTableWidgetItem(item[Info.Keys.vcodec]))
			self.ui.infoTableWidget.setItem(index, 2, QTableWidgetItem(item[Info.Keys.acodec]))
			self.ui.infoTableWidget.setItem(index, 3, QTableWidgetItem(item[Info.Keys.dimensions]))
			self.ui.infoTableWidget.setItem(index, 4, QTableWidgetItem(item[Info.Keys.size]))

	def lock_ui(self):
		self.disconnect_history_widget()
		self.ui.urlEdit.setDisabled(True)
		self.ui.getInfoButton.setDisabled(True)
		self.progressBar.reset()
		self.progressBar.setVisible(True)

	def unlock_ui(self):
		self.connect_history_widget()
		self.infoTableWidget_selectionChanged_slot()
		self.ui.urlEdit.setEnabled(True)
		self.urlEdit_textChanged()
		self.progressBar.reset()
		self.progressBar.setVisible(False)

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

	def enable_apply_and_cancel_buttons(self):
		self.ui.applyChangesButton.setEnabled(True)
		self.ui.cancelChangesButton.setEnabled(True)

	def disable_apply_and_cancel_buttons(self):
		self.ui.applyChangesButton.setEnabled(False)
		self.ui.cancelChangesButton.setEnabled(False)

	# Settings stuff
	def set_settings_core(self):
		self.core.set_ffmpeg_path(self.settings.ffmpeg_path.current)
		self.core.set_download_dir(self.settings.download_dir.current)
		self.core.set_player_path(self.settings.player_path.current)
		self.core.set_player_params(shlex.split(self.settings.player_params.current))

	def set_settings_ui(self):
		if self.settings.ffmpeg_path.current:
			self.ui.ffmpegPathEdit.setText(self.settings.ffmpeg_path.current)
		self.ui.ffmpegRadio.setEnabled(bool(self.settings.ffmpeg_path.current))

	def commit_settings(self):
		try:
			self.settings.ffmpeg_path.set(self.ui.ffmpegPathEdit.text().strip())
			self.settings.download_dir.set(self.ui.downloadDirEdit.text().strip())
			self.settings.player_path.set(self.ui.playerPathEdit.text().strip())
			self.settings.player_params.set(self.ui.playerParamsEdit.text().strip())
		except Exception as e:
			self.error_dialog_exec('Settings', str(e))
			return
		self.settings.save()

		self.set_settings_core()
		self.set_settings_ui()
		self.disable_apply_and_cancel_buttons()

	def undo_settings(self):
		self.ui.ffmpegPathEdit.setText(self.settings.ffmpeg_path.current)
		self.ui.downloadDirEdit.setText(self.settings.download_dir.current)
		self.ui.playerPathEdit.setText(self.settings.player_path.current)
		self.ui.playerParamsEdit.setText(self.settings.player_params.current)

		self.disable_apply_and_cancel_buttons()

	def pick_exe_ffmpeg(self):
		path = self.filepicker()
		if path:
			self.ui.ffmpegPathEdit.setText(path)
			self.enable_apply_and_cancel_buttons()

	def pick_exe_player(self):
		path = self.filepicker()
		if path:
			self.ui.playerPathEdit.setText(path)
			self.enable_apply_and_cancel_buttons()

	def filepicker(self):
		d = QFileDialog(parent=self, caption='Provide path to the executable')
		if d.exec_():
			path = d.selectedFiles()[0]
			return path
		else:
			return None

	def pick_download_dir(self):
		path = QFileDialog.getExistingDirectory(parent=self, caption='Provide path to the directory')
		if path:
			self.ui.downloadDirEdit.setText(path)
			self.enable_apply_and_cancel_buttons()

	def connect_signals(self):
		self.ui.getInfoButton.clicked.connect(self.getInfoButton_clicked)
		self.ui.urlEdit.textChanged.connect(self.urlEdit_textChanged)
		self.ui.downloadButton.clicked.connect(self.downloadButton_clicked)
		self.ui.streamButton.clicked.connect(self.streamButton_clicked)
		self.ui.infoTableWidget.itemDoubleClicked.connect(self.streamButton_clicked)
		self.ui.infoTableWidget.itemSelectionChanged.connect(
			self.infoTableWidget_selectionChanged_slot
		)

		self.connect_history_widget()

		self.ui.ffmpegPathEdit.textEdited.connect(self.enable_apply_and_cancel_buttons)
		self.ui.downloadDirEdit.textEdited.connect(self.enable_apply_and_cancel_buttons)
		self.ui.playerPathEdit.textEdited.connect(self.enable_apply_and_cancel_buttons)
		self.ui.playerParamsEdit.textEdited.connect(self.enable_apply_and_cancel_buttons)

		self.ui.ffmpegPathButton.clicked.connect(self.pick_exe_ffmpeg)
		self.ui.downloadDirButton.clicked.connect(self.pick_download_dir)
		self.ui.playerPathButton.clicked.connect(self.pick_exe_player)

		self.ui.applyChangesButton.clicked.connect(self.commit_settings)
		self.ui.cancelChangesButton.clicked.connect(self.undo_settings)

	def set_core_callbacks(self, core: Callbacks):
		core.task_finished_cb = self.task_finish
		core.set_progress_max_cb = self.set_progressBar_max
		core.set_progress_val_cb = self.set_progressBar_val
		core.show_msg_cb = self.show_status_msg
		core.redraw_cb = self.redraw

	def download_info(self, url: str):
		"""
		Download URL info, update tableWidget and history, reset playback
		information on success. Blocks UI.
		"""
		logging.debug(f"Loading info for {url}")
		self.ui.tabWidget.setDisabled(True)
		self.show_status_msg('Downloading info')
		self.redraw()

		try:
			self.core.download_info(url)

			self.update_table(self.core.get_info())
			self.setWindowTitle(self.window_title + ' :: ' + self.core.get_title())
			self.show_status_msg('Info loaded')

			self.history_add_item(self.core.get_title(), url)
		except Exception as e:
			self.error_dialog_exec('Info loading error', str(e))
			self.show_status_msg('Info loading error')

		self.ui.tabWidget.setDisabled(False)

	def disconnect_history_widget(self):
		if self.history_widget_connected:
			self.ui.historyView.doubleClicked.disconnect(self.history_item_clicked)
			self.history_widget_connected = False

	def connect_history_widget(self):
		if not self.history_widget_connected:
			self.ui.historyView.doubleClicked.connect(self.history_item_clicked)
			self.history_widget_connected = True

	def swap_d_s_buttons(self):
		if self.download_button_status:
			self.ui.downloadButton.clicked.disconnect(self.downloadButton_clicked)
			self.ui.downloadButton.clicked.connect(self.cancelButton_clicked)
			self.ui.downloadButton.setText('Stop')
		else:
			self.ui.downloadButton.clicked.disconnect(self.cancelButton_clicked)
			self.ui.downloadButton.clicked.connect(self.downloadButton_clicked)
			self.ui.downloadButton.setText(self.download_button_text)
		self.download_button_status = not self.download_button_status

	@pyqtSlot()
	def getInfoButton_clicked(self):
		self.download_info(self.ui.urlEdit.text().strip())

	@pyqtSlot(QModelIndex)
	def history_item_clicked(self, index: QModelIndex):
		"""Get URl from selected item and reload info."""
		assert self.ui.historyView.model() is not None
		url = self.ui.historyView.model().get_url(index)
		self.ui.urlEdit.setText(url)
		self.ui.tabWidget.setCurrentWidget(self.ui.mainTab)
		self.download_info(url)

	@pyqtSlot()
	def urlEdit_textChanged(self):
		"""Enable getInfoButton if urlEdit is not empty."""
		if not self.ui.urlEdit.text().strip():
			self.ui.getInfoButton.setEnabled(False)
		else:
			self.ui.getInfoButton.setEnabled(True)

	@pyqtSlot()
	def infoTableWidget_selectionChanged_slot(self):
		"""
		Enable streamButton and downloadButton if
		there are selected items in the tableWidget.
		"""
		if self.ui.infoTableWidget.selectedItems():
			if not self.core.is_download_blocked():
				self.ui.downloadButton.setEnabled(True)
			can_stream = bool(self.settings.ffmpeg_path.current) and bool(self.settings.player_path.current)
			self.ui.streamButton.setEnabled(can_stream)
		else:
			self.ui.downloadButton.setEnabled(False)
			self.ui.streamButton.setEnabled(False)

	@pyqtSlot()
	def downloadButton_clicked(self):
		"""Get selected formats and run selected downloader."""
		try:
			formats = self.get_selected_formats()
			logging.debug(f'Selected formats {formats}')
			self.core.set_format(formats)
			self.setWindowTitle(
				self.window_title + ' :: Downloading :: ' + self.core.get_title()
			)
			self.swap_d_s_buttons()
			self.lock_ui()

			# Check download directory
			if self.core.params.download_dir:
				os.makedirs(self.core.params.download_dir, exist_ok=True)
				if not os.access(self.core.params.download_dir, mode=os.W_OK):
					raise Exception('No permission to write to that directory')

			if self.ui.ytdlRadio.isChecked():
				self.core.download_with_ytdl()
			elif self.ui.ffmpegRadio.isChecked():
				self.core.download_with_ffmpeg()
			# elif self.ui.aria2Radio.isChecked():
			# 	self.core.download_with_aria2()

		except Exception as e:
			self.error_dialog_exec('Download Error', str(e))
			self.swap_d_s_buttons()
			self.unlock_ui()

	@pyqtSlot()
	def cancelButton_clicked(self):
		"""Send cancel signal to running downloader."""
		self.core.download_cancel()

	@pyqtSlot()
	def streamButton_clicked(self):
		"""Use FFmpeg downloader to stream selected items."""
		can_stream = bool(self.settings.ffmpeg_path.current) and bool(self.settings.player_path.current)
		if not can_stream:
			self.error_dialog_exec('Stream Error', 'Provide FFmpeg and player executables')
			return
		try:
			formats = self.get_selected_formats()
			logging.debug(f'Selected formats {formats}')
			self.core.set_format(formats)
			self.core.stream_target()
		except Exception as e:
			self.error_dialog_exec('Stream Error', str(e))

	# Asynchronous callbacks
	def task_finish(self, signal: Tuple[bool, str]):
		success, error_str = signal
		if not success:
			self.error_dialog_exec('Error', error_str)
		self.metaObject().invokeMethod(self, self._task_finish_helper.__name__, Qt.QueuedConnection)

	@pyqtSlot()
	def _task_finish_helper(self):
		self.set_alert()
		self.setWindowTitle(self.window_title + ' :: ' + self.core.get_title())
		self.swap_d_s_buttons()
		self.unlock_ui()

	def redraw(self):
		QApplication.processEvents()

	def set_progressBar_max(self, value: int):
		self.metaObject().invokeMethod(
			self.progressBar,
			self.progressBar.setMaximum.__name__,
			Qt.QueuedConnection,
			Q_ARG(int, value))

	def set_progressBar_val(self, value: int):
		self.metaObject().invokeMethod(
			self.progressBar,
			self.progressBar.setValue.__name__,
			Qt.QueuedConnection,
			Q_ARG(int, value))

	def show_status_msg(self, msg: str):
		self.metaObject().invokeMethod(
			self.statusBar(),
			self.statusBar().showMessage.__name__,
			Qt.QueuedConnection,
			Q_ARG(str, msg))

	def set_alert(self):
		self.metaObject().invokeMethod(
			self,
			self._set_alert_helper.__name__,
			Qt.QueuedConnection)

	@pyqtSlot()
	def _set_alert_helper(self):
		QApplication.alert(self, 0)

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
		msg_clean = MainWindow.ansi_esc.sub('', msg)
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
