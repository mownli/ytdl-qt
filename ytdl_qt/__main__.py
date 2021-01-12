#!/usr/bin/env python3

import argparse
import logging
import subprocess
import sys

from PyQt5.QtWidgets import QApplication
from pyperclip import paste

from ytdl_qt.core import Core
from ytdl_qt import utils
from ytdl_qt.qt_mainwindow import MainWindow


def check_ffmpeg():
	try:
		subprocess.run(
			[utils.Paths.get_ffmpeg_exe(), '-version'],
			check=True,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL
		)
	except Exception:
		MainWindow.error_dialog_exec('Error', 'Could not launch FFmpeg')
		sys.exit(1)


def main():
	logging.basicConfig(format='[%(levelname)s] %(module)s::%(funcName)s(): %(message)s')

	parser = argparse.ArgumentParser(description='GUI for youtube-dl.', prog='ytdl-qt.py')
	parser.add_argument('-d', help='debug', action='store_true')
	group = parser.add_mutually_exclusive_group()
	group.add_argument('url', metavar='URL', nargs='?')
	group.add_argument('-x', help='use clipboard', action='store_true')
	args = parser.parse_args()

	if args.x:
		url = paste()
	else:
		url = args.url

	if args.d:
		logging.getLogger().setLevel(level='DEBUG')

	app = QApplication([])
	# QApplication.setApplicationDisplayName(MainWindow.WINDOW_TITLE)

	check_ffmpeg()

	Core(url)

	sys.exit(app.exec_())


if __name__ == "__main__":
	main()
