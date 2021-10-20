#!/usr/bin/env python3

from typing import List

from yt_dlp import YoutubeDL
#from youtube_dl import YoutubeDL

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


class Info:

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
		url = 'webpage_url'
		format_url = 'url'
		ffmpeg_location = 'ffmpeg_location'

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

	def __init__(self, url: str, ytdl_params=None):
		assert url

		if ytdl_params is None:
			ytdl_params = {}

		with YoutubeDL(ytdl_params) as ytdl:
			self._info = ytdl.extract_info(url=url, download=False)

	def get_title(self):
		"""Return video title."""
		return self._info[Info.Keys.title]

	def get_url(self):
		return self._info[Info.Keys.url]

	def get_format_str(self, fmt_id_list: List[str]) -> str:
		if len(fmt_id_list) not in range(3):
			raise Exception('Two inputs max')

		if len(fmt_id_list) == 0:
			fmt_str = ''
		elif len(fmt_id_list) == 1:
			fmt_str = ''.join(fmt_id_list)
		else:
			fmt_dicts = []
			for fmt_id in fmt_id_list:
				for fmt_dict in self._info[Info.Keys.formats_received]:
					if fmt_dict[Info.Keys.id] == fmt_id:
						fmt_dicts.append(fmt_dict)
						break
			if check_dict_attribute(fmt_dicts[0], Info.Keys.vcodec) \
				and not check_dict_attribute(fmt_dicts[1], Info.Keys.vcodec):
				pass
			elif check_dict_attribute(fmt_dicts[1], Info.Keys.vcodec) \
				and not check_dict_attribute(fmt_dicts[0], Info.Keys.vcodec):
				first = fmt_dicts[0]
				fmt_dicts[0] = fmt_dicts[1]
				fmt_dicts[1] = first
			else:
				raise Exception('Unacceptable formats. Permitted combinations: video, audio, audio+video')
			fmt_str = f'{fmt_dicts[0][Info.Keys.id]}+{fmt_dicts[1][Info.Keys.id]}'
		return fmt_str

	def get_info_filtered(self):
		"""Return shortened	info as a list of dictionaries (id, vcodec, dim, acodec, size, url)."""
		# logging.debug(self._info)
		info_list = []
		if self._info:
			if Info.Keys.formats_received in self._info:
				for i in self._info[Info.Keys.formats_received]:
					fmt_dict = {Info.Keys.id: i[Info.Keys.id]}
					if check_dict_attribute(i, Info.Keys.vcodec):
						fmt_dict[Info.Keys.vcodec] = i[Info.Keys.vcodec]
					else:
						fmt_dict[Info.Keys.vcodec] = None

					fmt_dict[Info.Keys.dimensions] = None
					if check_dict_attribute(i, Info.Keys.height):
						if check_dict_attribute(i, Info.Keys.width):
							fmt_dict[Info.Keys.dimensions] = f"{i[Info.Keys.width]}x{i[Info.Keys.height]}"

					if check_dict_attribute(i, Info.Keys.acodec):
						fmt_dict[Info.Keys.acodec] = i[Info.Keys.acodec]
					else:
						fmt_dict[Info.Keys.acodec] = None

					if check_dict_attribute(i, Info.Keys.size):
						fmt_dict[Info.Keys.size] = convert_size(i[Info.Keys.size])
					else:
						fmt_dict[Info.Keys.size] = None

					# fmt_dict['url'] = i['url']
					fmt_dict[Info.Keys.protocol] = i[Info.Keys.protocol]

					info_list.append(fmt_dict)
			else:
				fmt_dict = {
					Info.Keys.id: None,
					Info.Keys.vcodec: None,
					Info.Keys.dimensions: None,
					Info.Keys.acodec: None,
					Info.Keys.size: None,
					Info.Keys.protocol: None
				}
				info_list.append(fmt_dict)

		return info_list

	def get_filename(self) -> str:
		"""Return prepared filename and extension in a tuple."""
		#return os.path.splitext(self.prepare_filename(self.info_internal))
		return self._info[Info.Keys.title]

	def get_format_url_list(self, fmt_ids: List[str]) -> List[str]:
		"""Return list of urls given the list of format ids."""
		url_list = []
		if Info.Keys.formats_received in self._info:
			for item in self._info[Info.Keys.formats_received]:
				if item[Info.Keys.id] in fmt_ids:
					url_list.append(item[Info.Keys.format_url])
		else:
			url_list = [self._info[Info.Keys.format_url]]
		return url_list

	def get_protocol_list(self, fmt_ids: List[str]) -> List[str]:
		"""Return list of protocols given the list of format ids."""
		assert self._info is not None
		protocol_list = []
		if Info.Keys.formats_received in self._info:
			for item in self._info[Info.Keys.formats_received]:
				if item[Info.Keys.id] in fmt_ids:
					protocol_list.append(item[Info.Keys.protocol])
		else:
			protocol_list = []
		return protocol_list
