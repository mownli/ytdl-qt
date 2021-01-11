#!/usr/bin/env python3

import math
import os
import pathlib


def convert_size(size_bytes):
	if size_bytes == 0:
		return "0B"
	size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
	i = int(math.floor(math.log(size_bytes, 1000)))
	p = math.pow(1000, i)
	s = round(size_bytes / p, 2)
	return f"{s}{size_name[i]}"


def check_dict_attribute(item, key):
	"""Needed for get_info()."""
	if (key in item) and (item[key] != 'none') and (item[key] is not None):
		return True
	else:
		return False


def build_ffmpeg_cmd(url_list, output_file=None, flv=False, force_ow=True, quiet=False):
	"""Return list with arguments for ffmpeg execution."""
	assert len(url_list) > 0
	ffmpeg_cmd = ['ffmpeg', '-hide_banner', '-nostdin']
	if quiet:
		ffmpeg_cmd += ['-loglevel', 'panic']
	if force_ow:
		ffmpeg_cmd.append('-y')
	else:
		ffmpeg_cmd.append('-n')
	for item in url_list:
		ffmpeg_cmd += ['-i', item]
	url_list_len = len(url_list)
	if url_list_len > 1:
		for i in range(0, url_list_len):
			# Maps all input streams into one output
			ffmpeg_cmd += ['-map', str(i)]
	# TODO: Figure out the AAC bullshit
	ffmpeg_cmd += ['-c', 'copy']
	if output_file is None:
		if flv:
			ffmpeg_cmd += ['-f', 'flv', '-']
		else:
			ffmpeg_cmd += ['-f', 'matroska', '-']
	else:
		ffmpeg_cmd.append(output_file)
	return ffmpeg_cmd


class Paths:

	application_name = 'ytdl-qt'
	history_file = 'url-history.csv'

	@staticmethod
	def get_history():
		if os.name == 'nt':
			return pathlib.Path(
				os.getenv('APPDATA'),
				Paths.application_name,
				Paths.history_file
			)
		elif os.name == 'posix':
			return pathlib.Path(
				os.getenv('XDG_DATA_HOME', default=f"{os.getenv('HOME')}/.local/share"),
				Paths.application_name,
				Paths.history_file
			)
		else:
			# Don't know about 'java'
			return None

	@staticmethod
	def get_mpv_exe():
		if os.name == 'nt':
			return 'mpv.exe'
		else:
			return 'mpv'

	@staticmethod
	def get_ffmpeg_exe():
		if os.name == 'nt':
			return 'mpv.exe'
		else:
			return 'mpv'

	@staticmethod
	def get_aria2c_exe():
		if os.name == 'nt':
			return 'aria2c.exe'
		else:
			return 'aria2c'
