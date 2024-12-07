#!/usr/bin/env python

from PyQt5 import QtCore, QtWidgets, QtGui, QtPrintSupport
from PIL import Image
import shutil
import os
import general_helpers

from pathlib import Path


class ImageViewer(QtWidgets.QMainWindow):
    # QMainWindow doesn't have a closed signal, so we'll make one.
    closed = QtCore.pyqtSignal()

    def __init__(self, parent, fileName, mode, table_data, main_target_dict, off_target_dict, seq_file):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.parent = parent
        self.printer = QtPrintSupport.QPrinter()

        self.scaleFactor = 0.0
        self.scale = 0.75
        offset = 50

        self.mode = mode
        self.home_location = Path().home() / "sifi" / "home"
        self.image_file = fileName
        self.table_data = table_data
        self.main_target_dict = main_target_dict
        self.off_target_dict = off_target_dict
        self.seq_file = seq_file

        self.imageLabel = QtWidgets.QLabel()
        self.imageLabel.setBackgroundRole(QtWidgets.QPalette.Base)
        self.imageLabel.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                QtWidgets.QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setBackgroundRole(QtWidgets.QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        self.setCentralWidget(self.scrollArea)
        self.createActions()
        self.createMenus()
        self.setWindowTitle("si-Fi Results")
        im = Image.open(self.image_file)
        self.resize((im.size[0]+offset-35)*self.scale, (im.size[1]+offset-7)*self.scale)
        self.open(self.image_file)


    def closeEvent(self, event):
        self.closed.emit()
        event.accept()

    def open(self, fileName):
        if fileName:
            image = QtWidgets.QImage(fileName)
            if image.isNull():
                QtWidgets.QMessageBox.information(self, "Image Viewer",
                        "Cannot load %s." % fileName)
                return
            self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(image))
            self.scaleFactor = 1.0
            self.printAct.setEnabled(True)
        self.scaleImage(self.scale)

    def print_(self):
        dialog = QtWidgets.QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QtWidgets.QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabel.pixmap().size()
            size.scale(rect.size(), QtCore.Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabel.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())

    def export_gbk(self):
        """Exports to genbank file."""
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', self.home_location, '*.gbk')
        if filename:
            if not str(filename).endswith('.gbk'):
                filename += filename + '.gbk'
            general_helpers.create_gbk(self.main_target_dict, self.off_target_dict, self.seq_file, filename)
            if os.path.exists(filename):
                message = 'Genbank file successfully saved!'
            else:
                message = 'Could not save genbank file!'
            self.show_info_message(message)

    def export_image(self):
        """Export the images as png."""
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', self.home_location, '*.png')
        if filename:
            if not str(filename).endswith('.png'):
                filename += filename + '.png'
            shutil.copy(self.image_file, filename)
            if os.path.exists(filename):
                message = 'Image successfully saved!'
            else:
                message = 'Could not save image!'
            self.show_info_message(message)


    def export_table(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Export table', self.home_location, '*.csv')
        if filename:
            if not str(filename).endswith('.csv'):
                filename += filename + '.csv'
            try:
                f_in = open(filename, 'w')
                f_in.write("Targets" + ';' + "Total siRNA hits" + ';' + "Efficient siRNA hits" + '\n')
                for data in self.table_data:
                    f_in.write(str(data[0]) + ';' + str(data[1]) + ';' + str(data[2]) + '\n')
                f_in.close()
                if os.path.exists(filename):
                    message = 'Table successfully saved!'
                else:
                    message = 'Could not save table!'
            except IOError:
                message = 'Permission denied! Please close the file.'

            self.show_info_message(message)

    def show_info_message(self, message):
        """Pop up an info message."""
        QtWidgets.QMessageBox.information(self,
                                      u"Information",
                                      message)


    def createActions(self):
        self.printAct = QtWidgets.QAction("&Print...", self, enabled=False, triggered=self.print_)
        self.exitAct = QtWidgets.QAction("E&xit", self, triggered=self.close)

        self.gbkAct = QtWidgets.QAction("Genbank file", self, triggered=self.export_gbk)
        self.imgAct = QtWidgets.QAction("Image file", self, triggered=self.export_image)
        self.tableAct = QtWidgets.QAction("Table (CSV)", self, triggered=self.export_table)

    def createMenus(self):

        self.fileMenu = QtWidgets.QMenu("&File", self)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        # Export menu
        self.exportMenu = QtWidgets.QMenu("&Save as", self)
        self.exportMenu.addAction(self.imgAct)

        self.exportMenu.addAction(self.tableAct)
        if self.mode == 0:
            self.exportMenu.addAction(self.gbkAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.exportMenu)

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))
