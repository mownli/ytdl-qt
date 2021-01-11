#!/usr/bin/env python3

import logging

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex

from ytdl_qt.history import History


class HistoryTableModel(QAbstractTableModel):

	def __init__(self, path_to_history, parent=None):
		super().__init__(parent)
		self._history = History(path_to_history)
		self._data = self._history.get_data_unique()

	def data(self, index, role=Qt.DisplayRole):
		# logging.debug('')
		if index.row() >= len(self._data):
			return None

		if role == Qt.DisplayRole:
			key = self._history.keys[index.column()]
			return self._data[len(self._data) - index.row() - 1][key]

	def rowCount(self, index):
		return len(self._data)

	def columnCount(self, index):
		return len(self._history.keys)

	def headerData(self, section, orientation, role):
		# logging.debug('')
		if role == Qt.DisplayRole:
			if orientation == Qt.Horizontal:
				return self._history.keys[section]
			else:
				return section

	def insertRows(self, row, count, dict_items, parent=None):
		logging.debug('')
		count = len(dict_items)
		self.beginInsertRows(QModelIndex(), row, row + count - 1)

		# for pos in range(0, count):
		# self._history.append_item(self._items_to_add[0])
		for item in dict_items:
			self._data.append(item)

		self.endInsertRows()

	def add_history_item(self, title, url):
		logging.debug('')
		assert title, url is not None
		# self._items_to_add = [{self._[0]: title, self._[1]: url}]
		# self.insertRows(0, 1)
		# self._items_to_add = []

		dict_item = {self._history.keys.title: title, self._history.keys.url: url}
		self._history.add_data(dict_item)

		index = self._history.index_of_unique(dict_item, self._history.keys.url)
		if index is not None:
			self._data.pop(index)
			self._data.append(dict_item)

			index_table = len(self._data) - index
			# 0 for the title column
			top_left_index = self.index(0, 0)
			bottom_right_index = self.index(index_table, 1)
			self.dataChanged.emit(top_left_index, bottom_right_index)
		else:
			list_arg = [dict_item]
			self.insertRows(0, len(list_arg), list_arg)

	def get_url(self, index):
		assert index is not None
		logging.debug(self._data[len(self._data) - index.row() - 1][self._history.keys.url])
		return self._data[len(self._data) - index.row() - 1][self._history.keys.url]