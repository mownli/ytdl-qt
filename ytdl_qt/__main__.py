#!/usr/bin/env python3

import argparse
import logging
import sys

from PyQt5.QtWidgets import QApplication

from ytdl_qt.qt_mainwindow import MainWindow


def main():
	logging.basicConfig(format='[%(levelname)s] %(module)s::%(funcName)s(): %(message)s')

	parser = argparse.ArgumentParser(description='GUI for youtube-dl.', prog='ytdl-qt.py')
	parser.add_argument('-d', help='debug', action='store_true')
	parser.add_argument('url', metavar='URL', nargs='?')
	args = parser.parse_args()

	if args.d:
		logging.getLogger().setLevel(level='DEBUG')

	app = QApplication(sys.argv)

	w = MainWindow()
	w.show()
	if args.url:
		w.ui.urlEdit.setText(args.url)
		w.download_info(args.url)

	sys.exit(app.exec())


if __name__ == "__main__":
	main()
