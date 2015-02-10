#!/usr/bin/env python
# coding=utf-8
# TODO dynamically display word list
# TODO recognize morphology
# TODO add offline MW11 data
# TODO add online dict from youdao and webster
import os
import sys
import sqlite3
import ConfigParser

from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from PyQt4.QtCore import *


class Config:
    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.config.optionxform = str
        self.config.read('config.ini')
        self.database_ec = self.config.get('General', 'database_ec')
        self.search_online = self.config.get('General', 'search_online')
        self.voice_dir = self.config.get('General', 'voice_directory')
        self.voice_autoplay = self.config.getboolean('General', 'voice_autoplay')

    def writeConfig(self):
        with open('config.ini', 'w') as config_file:
            self.config.write(config_file)


class ZDict(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.config = Config()
        self.conn = sqlite3.connect(self.config.database_ec)
        self.createLayout()
        self.createConnection()

    def search(self):
        self.word = str(self.wordBar.text())
        self.getBasicEC()
        self.showHTML()
        if self.config.voice_autoplay:
            self.readAloud()

    def createLayout(self):
        self.setWindowTitle("zDict")
        self.wordBar = QLineEdit()
        self.goButton = QPushButton("Search")
        self.voiceButton = QPushButton("Read")
        self.settingButton = QPushButton("Setting")
        bl = QHBoxLayout()
        bl.addWidget(self.wordBar)
        bl.addWidget(self.goButton)
        bl.addWidget(self.voiceButton)
        bl.addWidget(self.settingButton)

        self._page = QWebPage()
        self._view = QWebView()
        self._view.setPage(self._page)
        self._window = QMainWindow()
        self._window.setCentralWidget(self._view)
        layout = QVBoxLayout()
        layout.addLayout(bl)
        layout.addWidget(self._window)

        self.setLayout(layout)

    def createConnection(self):
        self.connect(self.wordBar, SIGNAL('returnPressed()'), self.search)
        self.connect(self.wordBar, SIGNAL('returnPressed()'), self.wordBar, SLOT('selectAll()'))
        self.connect(self.goButton, SIGNAL('clicked()'), self.search)
        self.connect(self.goButton, SIGNAL('clicked()'), self.wordBar, SLOT('selectAll()'))
        self.connect(self.voiceButton, SIGNAL('clicked()'), self.readAloud)
        self.connect(self.settingButton, SIGNAL('clicked()'), self.setting)

    def getBasicEC(self):
        cursor = self.conn.execute("SELECT basic_ec FROM dict WHERE word = '%s';" % self.word.replace("'", "''"))
        data = cursor.fetchone()
        if data == None:
            self.meaning = ''
        else:
            self.meaning = data[0].encode('utf-8')
        print self.meaning

    def showHTML(self):
        self._view.setHtml(self.meaning.decode('utf-8'))
        self._view.show()

    def readAloud(self):
        voice_file = self.config.voice_dir + '/%s/%s.wav' % (self.word[0], self.word)
        if os.path.exists(voice_file):
            QSound.play(voice_file)

    def setting(self):
        self.setting_window = Setting()
        self.setting_window.setFixedSize(400, 400)
        self.setting_window.setWindowTitle('zDict Setting')
        self.setting_window.show()

    def closeEvent(self, event):
        self.config.writeConfig()
        sys.exit()


class Setting(QWidget):
    def __init__(self):
        QWidget.__init__(self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dict = ZDict()
    dict.show()
    app.exec_()
