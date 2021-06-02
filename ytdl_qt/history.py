#!/usr/bin/env python

import csv
import logging
import pathlib


class History:

	class _Keys:

		url = 'url'
		title = 'title'

		# Don't change the order
		_keys = [title, url]

		def __init__(self):
			pass

		def __getitem__(self, item):
			return self._keys[item]

		def __len__(self):
			return len(self._keys)

	def __init__(self, path: pathlib.Path):
		self.keys = self._Keys()
		self._data = []
		self._data_set = []
		self._path = path
		if path.is_file():
			self._read_all_from_storage()
		else:
			path.parent.mkdir(parents=True, exist_ok=True)
			path.touch()
			logging.debug(f'Created history file at {path}')

	def index_of_unique(self, item, key):
		"""Return index or None."""
		for index, _dict in enumerate(self._data_set):
			if _dict[key] == item[key]:
				return index
		return None

	def _add_data_unique(self, new_item):
		"""Add unique data. Doesn't write to storage."""
		for item in self._data_set:
			if item[self.keys.url] == new_item[self.keys.url]:
				self._data_set.remove(item)
				break
		self._data_set.append(new_item)

	def get_data_unique(self):
		return self._data_set

	def add_data(self, new_item):
		"""Add data. Writes to storage."""
		self._data.append(new_item)
		self._append_to_storage(new_item)

	def _read_all_from_storage(self):
		logging.debug(f'Reading from {self._path}')
		with open(self._path, newline='') as csvfile:
			reader = csv.reader(csvfile, delimiter=',', quotechar='\"')
			for row in reader:
				row_dict = {}
				for index, key in enumerate(self.keys):
					row_dict[key] = row[index]
				self._data.append(row_dict)
				self._add_data_unique(row_dict)

	def _write_all_from_storage(self):
		"""Writes data to disc."""
		with open(self._path, 'w', newline='') as csvfile:
			writer = csv.writer(csvfile, delimiter=',', quotechar='\"', quoting=csv.QUOTE_ALL)
			for row in self._data:
				writer.writerow(row.values())

	def _append_to_storage(self, item):
		assert item is not None
		with open(self._path, 'a', newline='') as csvfile:
			writer = csv.writer(csvfile, delimiter=',', quotechar='\"', quoting=csv.QUOTE_ALL)
			writer.writerow(item.values())
