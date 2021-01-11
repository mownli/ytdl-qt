TARGET = ytdl-qt.pyz
INSTALLDIR = ~/.local/bin
PYTHON = /usr/bin/env python3
SRCDIR = ytdl_qt
BUILDDIR=build

pyz: $(SRCDIR)
	mkdir -p $(BUILDDIR)
	cp -r $(SRCDIR)/* -t $(BUILDDIR)
	cd $(BUILDDIR); find . -type f -exec sed -i "s/from ytdl_qt\./from /g" {} +
	cd $(BUILDDIR); find . -type f -exec sed -i "s/from ytdl_qt //g" {} +
	cd $(BUILDDIR); zip -q tmp.zip *
	echo "#!$(PYTHON)" > $(BUILDDIR)/$(TARGET)
	cat $(BUILDDIR)/tmp.zip >> $(BUILDDIR)/$(TARGET)
	chmod u+x $(BUILDDIR)/$(TARGET)

install: $(BUILDDIR)/$(TARGET)
	install $^ $(INSTALLDIR)/$(TARGET)

clean:
	rm -f $(TARGET)
	rm -rf build
	rm -rf dist
	rm -rf ytdl_qt.egg-info

wheel: $(SRCDIR)
	python setup.py bdist_wheel

forms:
	pyuic5 resources/qt_mainwindow_form.ui > $(SRCDIR)/qt_mainwindow_form.py