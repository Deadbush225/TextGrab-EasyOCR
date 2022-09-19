import sys
import os
import tempfile
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QObject, Qt, pyqtSlot, pyqtSignal, QThread
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QVBoxLayout, QWidget, QShortcut,\
    QPushButton, QTextEdit, QLineEdit, QFormLayout, QHBoxLayout, QCheckBox, QSpinBox, QDoubleSpinBox
from pynput.mouse import Controller

from PIL import ImageGrab, Image
import numpy as np
from screeninfo import get_monitors

import easyocr

QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)



class App(QWidget):
    isProcessing = False

    def __init__(self):
        super().__init__()
        # self.args = args
        # self.model = cli.LatexOCR(self.args)
        self.initUI()
        self.initOCR()
        self.snipWidget = SnipWidget(self)
        self.snipWidget.snipped.connect(self.returnSnip)
        self.show()

    def initUI(self):
        self.setWindowTitle("LaTeX OCR")
        # QApplication.setWindowIcon(QtGui.QIcon(':/icons/icon.svg'))
        self.left = 300
        self.top = 300
        self.width = 500
        self.height = 300
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Create snip button
        self.snipButton = QPushButton('Snip [Alt+S]', self)
        self.snipButton.clicked.connect(self.onClick)

        self.shortcut = QShortcut(QKeySequence("Alt+S"), self)
        self.shortcut.activated.connect(self.onClick)

        # Create retry button
        self.closeButton = QPushButton('Close', self)
        self.closeButton.clicked.connect(self.close)

        # Create layout
        buttons = QVBoxLayout()
        buttons.addWidget(self.snipButton)
        buttons.addWidget(self.closeButton)
        self.setLayout(buttons)

    def initOCR(self):
        # self.reader = ""
        self.reader = easyocr.Reader(['en'])

    def toggleProcessing(self, value=None):
        if value is None:
            self.isProcessing = not self.isProcessing
        else:
            self.isProcessing = value
        if self.isProcessing:
            text = 'Interrupt'
            func = self.interrupt
        else:
            text = 'Snip [Alt+S]'
            func = self.onClick
            self.retryButton.setEnabled(True)
        self.shortcut.setEnabled(not self.isProcessing)
        self.snipButton.setText(text)
        self.snipButton.clicked.disconnect()
        self.snipButton.clicked.connect(func)
        self.displayPrediction()

    # @pyqtSlot()
    def onClick(self):
        self.close()
        self.snipWidget.snip()

    # @pyqtSlot()
    def returnPrediction(self, result):
        print(3)
        # self.toggleProcessing(False)
        # success, prediction = result["success"], result["prediction"]

        # if success:
        #     self.displayPrediction(prediction)
        #     self.retryButton.setEnabled(True)
        # else:
        #     self.webView.setHtml("")
        #     msg = QMessageBox()
        #     msg.setWindowTitle(" ")
        #     msg.setText("Prediction failed.")
        #     msg.exec_()
        
        print(f"result: {result}")

        clipboard = QApplication.clipboard()
        clipboard.clear()
        clipboard.setText(result, clipboard.Clipboard)

    def returnSnip(self, img):
        # self.toggleProcessing(True)
        # self.retryButton.setEnabled(False)

        # self.show()
        # try:
        #     self.model.args.temperature = self.tempField.value()
        #     if self.model.args.temperature == 0:
        #         self.model.args.temperature = 1e-8
        # except:
        #     pass

        # Run the model in a separate thread
        self.thread_ = ModelThread(self, img=img)
        self.thread_.finished.connect(self.returnPrediction)
        # self.thread.finished.connect(self.thread.deleteLater)
        print(0)
        self.thread_.start()

class ModelThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, parent, img):
        super().__init__()
        self.img = img
        self.parent_ = parent

    def run(self):
        # try:
        #     prediction = self.model(self.img)
        #     # replace <, > with \lt, \gt so it won't be interpreted as html code
        #     prediction = prediction.replace('<', '\\lt ').replace('>', '\\gt ')
        #     self.finished.emit({"success": True, "prediction": prediction})
        # except Exception as e:
        #     import traceback
        #     traceback.print_exc()
        #     self.finished.emit({"success": False, "prediction": None})
        
        # print(type(self.img))
        print(1)
        result = self.parent_.reader.readtext(self.img, detail = 0)
        print(result)
        s = " ".join(result)
        print(s)
        self.finished.emit(s)
        print(2)


class SnipWidget(QMainWindow):
    isSnipping = False
    snipped = pyqtSignal(np.ndarray)

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        monitos = get_monitors()
        bboxes = np.array([[m.x, m.y, m.width, m.height] for m in monitos])
        x, y, _, _ = bboxes.min(0)
        w, h = bboxes[:, [0, 2]].sum(1).max(), bboxes[:, [1, 3]].sum(1).max()
        self.setGeometry(x, y, w-x, h-y)

        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()

        self.mouse = Controller()

    def snip(self):
        self.isSnipping = True
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))

        self.show()

    def paintEvent(self, event):
        if self.isSnipping:
            brushColor = (0, 180, 255, 100)
            opacity = 0.3
        else:
            brushColor = (255, 255, 255, 0)
            opacity = 0

        self.setWindowOpacity(opacity)
        qp = QtGui.QPainter(self)
        qp.setPen(QtGui.QPen(QtGui.QColor('black'), 2))
        qp.setBrush(QtGui.QColor(*brushColor))
        qp.drawRect(QtCore.QRect(self.begin, self.end))

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            QApplication.restoreOverrideCursor()
            self.close()
            self.parent.show()
        event.accept()

    def mousePressEvent(self, event):
        self.startPos = self.mouse.position

        self.begin = event.pos()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.isSnipping = False
        QApplication.restoreOverrideCursor()

        startPos = self.startPos
        endPos = self.mouse.position
        # account for retina display. #TODO how to check if device is actually using retina display
        factor = 2 if sys.platform == "darwin" else 1

        x1 = int(min(startPos[0], endPos[0])*factor)
        y1 = int(min(startPos[1], endPos[1])*factor)
        x2 = int(max(startPos[0], endPos[0])*factor)
        y2 = int(max(startPos[1], endPos[1])*factor)

        self.repaint()
        QApplication.processEvents()
        try:
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
        except Exception as e:
            if sys.platform == "darwin":
                img = ImageGrab.grab(bbox=(x1//factor, y1//factor, x2//factor, y2//factor), all_screens=True)
            else:
                raise e
        QApplication.processEvents()

        self.close()
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        # self.parent.returnSnip(np.array(img))
        self.snipped.emit(np.array(img))

def main():
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)

if __name__ == "__main__":

    import sys
    sys.excepthook = except_hook

    main()