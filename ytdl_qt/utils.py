#!/usr/bin/env python3

import math
import subprocess


def convert_size(size_bytes):
	if size_bytes == 0:
		return "0B"
	size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
	i = int(math.floor(math.log(size_bytes, 1000)))
	p = math.pow(1000, i)
	s = round(size_bytes / p, 2)
	return f"{s}{size_name[i]}"


def check_dict_attribute(item, key):
	if key in item:
		stuff = item[key]
		if stuff != 'none' and stuff is not None:
			return True
	return False


def check_ffmpeg(path: str) -> bool:
	try:
		subprocess.run(
			[path, '-version'],
			check=True,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL
		)
		return True
	except Exception:
		return False


def build_ffmpeg_args_list(url_list, output_file=None, flv=False, force_ow=True, quiet=False, quoted=False):
	"""Return list with arguments for ffmpeg execution."""
	assert len(url_list) > 0
	ffmpeg_cmd = ['-hide_banner', '-nostdin']
	if quiet:
		ffmpeg_cmd += ['-loglevel', 'panic']
	if force_ow:
		ffmpeg_cmd.append('-y')
	else:
		ffmpeg_cmd.append('-n')
	for item in url_list:
		ffmpeg_cmd += ['-i', f"\"{item}\"" if quoted else item]
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
		ffmpeg_cmd.append(f"\"{output_file}\"" if quoted else output_file)
	return ffmpeg_cmd
