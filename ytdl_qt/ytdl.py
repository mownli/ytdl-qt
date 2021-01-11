#!/usr/bin/env python3

import logging
import os

from youtube_dl import YoutubeDL

from ytdl_qt.utils import check_dict_attribute, convert_size


# class LoggerForYtdl(object):
# 	def debug(self, msg):
# 		print(msg)
#
# 	def warning(self, msg):
# 		print(msg)
#
# 	def error(self, msg):
# 		print(msg)

class Ytdl(YoutubeDL):

	class Keys:

		vcodec = 'vcodec'
		acodec = 'acodec'
		dimensions = 'dim'
		height = 'height'
		width = 'width'
		size = 'filesize'
		protocol = 'protocol'
		format_requested = 'format'
		formats_received = 'formats'
		id = 'format_id'
		hooks = 'progress_hooks'
		title = 'title'
		url = 'url'

		# For hooks
		eta = 'eta'
		status = 'status'
		total_bytes = 'total_bytes'
		total_bytes_estimate = 'total_bytes_estimate'
		downloaded_bytes = 'downloaded_bytes'
		downloading = 'downloading'
		finished = 'finished'
		filename = 'filename'
		error = 'error'

	def __init__(self):
		# params = {'logger': LoggerForYtdl()}
		params = {'noplaylist': True, 'forcefilename': True}
		YoutubeDL.__init__(self, params=params)
		self._info = None
		self._current_url = None
		self._fmt_id_selection = []
		self._number_of_files_to_download = 0

	def download_info(self, url):
		"""Downloads full info."""
		self.reset_format()
		info = self.extract_info(url, download=False)
		self._current_url = url
		self._info = info
		logging.debug(info)

	def set_format(self, fmt_id_list):
		"""Sorts and sets format ids previously returned by YoutubeDL to download."""
		assert self._info is not None
		if len(fmt_id_list) not in range(0, 3):
			raise Exception('Two inputs max')

		if len(fmt_id_list) == 0:
			fmt_str = None
		elif len(fmt_id_list) == 1:
			fmt_str = ''.join(fmt_id_list)
		else:
			fmt_dicts = []
			for fmt_id in fmt_id_list:
				for fmt_dict in self._info[self.Keys.formats_received]:
					if fmt_dict[self.Keys.id] == fmt_id:
						fmt_dicts.append(fmt_dict)
						break
			fmt_str = ''
			if check_dict_attribute(fmt_dicts[0], self.Keys.vcodec) and not check_dict_attribute(fmt_dicts[1], self.Keys.vcodec):
				fmt_str = f"{fmt_dicts[0][self.Keys.id]}+{fmt_dicts[1][self.Keys.id]}"
			elif check_dict_attribute(fmt_dicts[1], self.Keys.vcodec) and not check_dict_attribute(fmt_dicts[0], self.Keys.vcodec):
				fmt_str = f"{fmt_dicts[1][self.Keys.vcodec]}+{fmt_dicts[0][self.Keys.vcodec]}"
			else:
				raise Exception('Unacceptable formats. Permitted combinations: video, audio, audio+video')
		logging.debug(f"fmt_str: {fmt_str}")
		self.params[self.Keys.format_requested] = fmt_str
		self._fmt_id_selection = fmt_id_list
		if len(fmt_id_list) == 0:
			self._number_of_files_to_download = 1
		else:
			self._number_of_files_to_download = len(fmt_id_list)

	def set_progress_hooks(self, ph_list):
		self.params[self.Keys.hooks] = ph_list

	def reset_format(self):
		self.params[self.Keys.format_requested] = None

	def get_current_url(self):
		"""Return current stored url."""
		assert self._current_url is not None
		return self._current_url

	def get_title(self):
		"""Return video title."""
		assert self._info is not None
		return self._info[self.Keys.title]

	def get_filename(self):
		"""Return prepared filename and extension in a tuple."""
		assert self._info is not None
		return os.path.splitext(self.prepare_filename(self._info))

	def get_info(self):
		"""Return shortened	info as a list of dictionaries (id, vcodec, dim, acodec, size, url)."""
		assert self._info is not None
		# logging.debug(self._info)
		info_list = []
		if self._info:
			if self.Keys.formats_received in self._info:
				for i in self._info[self.Keys.formats_received]:
					fmt_dict = {self.Keys.id: i[self.Keys.id]}
					if check_dict_attribute(i, self.Keys.vcodec):
						fmt_dict[self.Keys.vcodec] = i[self.Keys.vcodec]
					else:
						fmt_dict[self.Keys.vcodec] = None

					fmt_dict[self.Keys.dimensions] = None
					if check_dict_attribute(i, self.Keys.height):
						if check_dict_attribute(i, self.Keys.width):
							fmt_dict[self.Keys.dimensions] = f"{i[self.Keys.width]}x{i[self.Keys.height]}"

					if check_dict_attribute(i, self.Keys.acodec):
						fmt_dict[self.Keys.acodec] = i[self.Keys.acodec]
					else:
						fmt_dict[self.Keys.acodec] = None

					if check_dict_attribute(i, self.Keys.size):
						fmt_dict[self.Keys.size] = convert_size(i[self.Keys.size])
					else:
						fmt_dict[self.Keys.size] = None

					# fmt_dict['url'] = i['url']
					fmt_dict[self.Keys.protocol] = i[self.Keys.protocol]

					info_list.append(fmt_dict)
			else:
				fmt_dict = {
					self.Keys.id: None,
					self.Keys.vcodec: None,
					self.Keys.dimensions: None,
					self.Keys.acodec: None,
					self.Keys.size: None,
					# 'url': self._current_url,
					self.Keys.protocol: None
				}
				info_list.append(fmt_dict)

		return info_list

	def get_url_selection(self):
		return self.get_url_list_by_ids(self._fmt_id_selection)

	def get_url_list_by_ids(self, fmt_id_list):
		"""Return list of urls given the list of format ids."""
		assert self._info is not None
		url_list = []
		if self.Keys.formats_received in self._info:
			for item in self._info[self.Keys.formats_received]:
				if item[self.Keys.id] in fmt_id_list:
					url_list.append(item[self.Keys.url])
		else:
			url_list = [self._info[self.Keys.url]]
		return url_list

	def get_protocol_selection(self):
		return self._get_protocol_list_by_ids(self._fmt_id_selection)

	def _get_protocol_list_by_ids(self, fmt_id_list):
		"""Return list of protocols given the list of format ids."""
		assert self._info is not None
		protocol_list = []
		if self.Keys.formats_received in self._info:
			for item in self._info[self.Keys.formats_received]:
				if item[self.Keys.id] in fmt_id_list:
					protocol_list.append(item[self.Keys.protocol])
		else:
			protocol_list = []
		return protocol_list

	def get_number_of_files_to_download(self):
		return self._number_of_files_to_download

	# def download_target(self):
	# 	assert self._info is not None
	# 	#self.process_ie_result(self._info)
	# 	# self._info['requested_formats'] = (self._info['formats'][0], )
	# 	# self.process_info(self._info)
