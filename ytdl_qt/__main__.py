#!/usr/bin/env python3

import argparse
import logging
import sys

from pyperclip import paste

from ytdl_qt.qt_wrapper import QtWrapper


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

	app = QtWrapper()
	sys.exit(app.exec(url))


if __name__ == "__main__":
	main()
