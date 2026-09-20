#!/usr/bin/env python3
"""Airwave — a small native Wayland radio and music player."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from PySide6.QtCore import Qt, QProcess, QTimer, QSettings
from PySide6.QtNetwork import QLocalSocket
from PySide6.QtGui import QColor, QPainter, QPen, QShortcut, QKeySequence
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QSlider, QFileDialog, QInputDialog, QMessageBox, QFrame)

PRESETS = [
    ('Groove Salad', 'Ambient · Downtempo', 'https://somafm.com/groovesalad.pls'),
    ('Drone Zone', 'Atmospheric · Ambient', 'https://somafm.com/dronezone.pls'),
    ('ROCK ANTENNE', 'Rock · Germany', 'https://stream.rockantenne.de/rockantenne/stream/mp3'),
    ('Hotmix Hits', 'Pop · Chart hits', 'https://streaming.hotmixradio.com/hotmix-hits-en-mp3'),
    ('Back2HipHop Radio', 'Hip hop · Old school', 'https://radio.back2hiphop.fr/listen/back2hiphop_radio/radio.mp3'),
    ('Hotmix Lo-Fi', 'Lo-fi · Chill beats', 'https://streaming.hotmixradio.com/hotmix-lofi-en-mp3'),
]

class Dial(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(155)
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(QPen(QColor('#334548'), 1))
        for i in range(51):
            x = 20 + (w - 40) * i / 50
            y = 58 if i % 5 == 0 else 72
            p.drawLine(int(x), y, int(x), 94)
        p.setPen(QPen(QColor('#b7eb93'), 3))
        p.drawLine(int(w * .57), 35, int(w * .57), 110)
        p.setPen(QColor('#839994'))
        for i, t in enumerate(['88', '92', '96', '100', '104', '108']):
            p.drawText(int(15 + (w - 48) * i / 5), 132, t)

class Player(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('Airwave', 'Airwave')
        self.setWindowTitle('Airwave — Radio & Music')
        self.setMinimumSize(800, 650)
        self.resize(940, 650)
        self.current = None
        self.paused = False
        self.ready = False
        self.buffer = b''
        self.stations = list(PRESETS)
        try:
            saved = json.loads(self.settings.value('stations', '[]'))
            self.stations += [tuple(s) for s in saved if isinstance(s, list) and len(s) == 3 and all(isinstance(v, str) for v in s)]
        except (ValueError, TypeError):
            pass
        self.build_ui()
        self.temp = tempfile.TemporaryDirectory(prefix='airwave-')
        self.socket_path = self.temp.name + '/mpv.sock'
        self.socket = QLocalSocket(self)
        self.socket.connected.connect(self.connected)
        self.socket.readyRead.connect(self.read_messages)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(lambda: self.process.readAllStandardOutput())
        self.process.errorOccurred.connect(lambda _: self.status.setText('Could not start mpv. Check that it is installed.'))
        self.process.finished.connect(lambda *_: self.engine_stopped())
        self.process.start('mpv', ['--no-config', '--idle=yes', '--no-video', '--terminal=no',
            '--audio-display=no', '--input-ipc-server=' + self.socket_path,
            '--volume=' + str(self.volume.value())])
        self.connect_attempts = 0
        self.retry = QTimer(self)
        self.retry.timeout.connect(self.try_connect)
        self.retry.start(100)
        QShortcut(QKeySequence('Ctrl+O'), self, activated=self.open_file)
        QShortcut(QKeySequence('Ctrl+F'), self, activated=self.search.setFocus)
        QShortcut(QKeySequence('Ctrl+Space'), self, activated=self.toggle)

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(28, 24, 28, 24)
        main.setSpacing(18)
        header = QHBoxLayout()
        title = QLabel('airwave<span style="color:#b7eb93"> / </span>')
        title.setObjectName('brand')
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QLabel('INTERNET RADIO  /  MUSIC'))
        main.addLayout(header)
        body = QHBoxLayout()
        body.setSpacing(26)
        left = QVBoxLayout()
        left.addWidget(QLabel('YOUR FREQUENCIES'))
        self.search = QLineEdit()
        self.search.setPlaceholderText('Filter stations…')
        self.search.textChanged.connect(self.refresh)
        left.addWidget(self.search)
        self.list = QListWidget()
        self.list.setMinimumWidth(230)
        self.list.setMaximumWidth(330)
        self.list.itemClicked.connect(self.choose)
        left.addWidget(self.list)
        add = QPushButton('+  Add station')
        add.clicked.connect(self.add_station)
        left.addWidget(add)
        remove = QPushButton('Remove custom station')
        remove.clicked.connect(self.remove_station)
        left.addWidget(remove)
        body.addLayout(left, 2)
        right = QVBoxLayout()
        card = QFrame()
        card.setObjectName('card')
        content = QVBoxLayout(card)
        content.setContentsMargins(28, 26, 28, 26)
        self.badge = QLabel('●  READY TO TUNE IN')
        self.badge.setObjectName('badge')
        content.addWidget(self.badge)
        content.addStretch()
        self.name = QLabel('Find your\nfrequency.')
        self.name.setObjectName('station')
        self.name.setWordWrap(True)
        self.name.setMinimumHeight(100)
        content.addWidget(self.name)
        self.track = QLabel('Choose a station and settle in.')
        self.track.setWordWrap(True)
        self.track.setTextFormat(Qt.PlainText)
        content.addWidget(self.track)
        content.addWidget(Dial())
        self.status = QLabel('Starting audio engine…')
        self.status.setWordWrap(True)
        content.addWidget(self.status)
        content.addStretch()
        right.addWidget(card, 1)
        controls = QHBoxLayout()
        self.play = QPushButton('▶  Play')
        self.play.setObjectName('play')
        self.play.setEnabled(False)
        self.play.clicked.connect(self.toggle)
        controls.addWidget(self.play)
        stop = QPushButton('■  Stop')
        stop.clicked.connect(self.stop)
        controls.addWidget(stop)
        local = QPushButton('Open music')
        local.clicked.connect(self.open_file)
        controls.addWidget(local)
        right.addLayout(controls)
        volume_row = QHBoxLayout()
        volume_row.addWidget(QLabel('VOLUME'))
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(int(self.settings.value('volume', 65)))
        self.volume.valueChanged.connect(self.set_volume)
        volume_row.addWidget(self.volume)
        self.volume_label = QLabel(str(self.volume.value()) + '%')
        volume_row.addWidget(self.volume_label)
        right.addLayout(volume_row)
        body.addLayout(right, 3)
        main.addLayout(body, 1)
        footer = QLabel('SomaFM presets  •  Add any HTTP(S) radio stream  •  Ctrl+O open music')
        footer.setObjectName('footer')
        main.addWidget(footer)
        self.refresh()

    def refresh(self):
        self.list.clear()
        query = self.search.text().casefold()
        for station in self.stations:
            if query in (station[0] + ' ' + station[1]).casefold():
                item = QListWidgetItem(station[0] + '\n' + station[1])
                item.setData(Qt.UserRole, station)
                self.list.addItem(item)

    def persist(self):
        self.settings.setValue('stations', json.dumps([s for s in self.stations if s not in PRESETS]))
        self.refresh()

    def add_station(self):
        name, ok = QInputDialog.getText(self, 'Add a station', 'Station name:')
        if not ok or not name.strip(): return
        url, ok = QInputDialog.getText(self, 'Stream address', 'HTTP(S) stream or playlist URL:')
        if not ok: return
        from urllib.parse import urlparse
        parsed = urlparse(url.strip())
        if parsed.scheme not in ('http', 'https') or not parsed.hostname:
            QMessageBox.warning(self, 'Invalid stream', 'Enter a valid http:// or https:// stream URL.')
            return
        self.stations.append((name.strip(), 'Custom station', url.strip()))
        self.persist()

    def remove_station(self):
        item = self.list.currentItem()
        if not item: return
        station = tuple(item.data(Qt.UserRole))
        if station in PRESETS: return
        self.stations.remove(station)
        self.persist()

    def try_connect(self):
        self.connect_attempts += 1
        if self.connect_attempts > 80:
            self.retry.stop()
            self.status.setText('Audio engine unavailable. Close and reopen Airwave.')
        elif self.socket.state() == QLocalSocket.UnconnectedState:
            self.socket.connectToServer(self.socket_path)

    def connected(self):
        self.retry.stop()
        self.ready = True
        self.play.setEnabled(True)
        self.status.setText('Select a station to start listening.')
        for i, prop in enumerate(['metadata', 'pause', 'paused-for-cache']):
            self.command('observe_property', i + 1, prop)
        if self.current: self.load(self.current)

    def command(self, *args):
        if self.ready:
            self.socket.write((json.dumps({'command': list(args)}) + '\n').encode())
            self.socket.flush()

    def choose(self, item):
        self.load(tuple(item.data(Qt.UserRole)))

    def load(self, station):
        self.current = station
        self.name.setTextFormat(Qt.PlainText)
        self.name.setText(station[0])
        self.track.setText(station[1])
        self.status.setText('Connecting…')
        self.badge.setText('●  TUNING IN')
        self.paused = False
        self.play.setText('Ⅱ  Pause')
        self.command('set_property', 'pause', False)
        self.command('loadfile', station[2], 'replace')

    def toggle(self):
        if not self.current:
            item = self.list.currentItem() or self.list.item(0)
            if item: self.choose(item)
        else:
            self.command('cycle', 'pause')

    def stop(self):
        self.command('stop')
        self.current = None
        self.paused = False
        self.play.setText('▶  Play')
        self.badge.setText('●  OFF AIR')
        self.status.setText('Stopped. Choose a station to listen again.')

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Open music', str(Path.home()),
            'Audio (*.mp3 *.flac *.ogg *.opus *.wav *.m4a *.aac);;All files (*)')
        if filename: self.load((Path(filename).stem, 'Local music', filename))

    def set_volume(self, value):
        self.volume_label.setText(str(value) + '%')
        self.command('set_property', 'volume', value)
        self.settings.setValue('volume', value)

    def engine_stopped(self):
        self.ready = False
        self.play.setEnabled(False)
        self.status.setText('Audio engine stopped. Reopen Airwave to reconnect.')

    def read_messages(self):
        self.buffer += bytes(self.socket.readAll())
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            try: msg = json.loads(line)
            except ValueError: continue
            event = msg.get('event')
            if event == 'file-loaded':
                self.badge.setText('●  ON AIR' if self.current and self.current[2].startswith('http') else '●  PLAYING')
                self.status.setText('Playing')
            elif event == 'end-file' and msg.get('reason') in ('error', 'eof'):
                self.status.setText('Stream unavailable. Try another station or press Play to retry.' if msg.get('reason') == 'error' else 'Playback finished.')
                self.badge.setText('●  OFF AIR')
                self.current = None
                self.play.setText('▶  Play')
            elif event == 'property-change':
                prop, value = msg.get('name'), msg.get('data')
                if prop == 'metadata' and value:
                    title = value.get('icy-title') or value.get('title') or value.get('TITLE')
                    if title: self.track.setText(title)
                elif prop == 'pause':
                    self.paused = bool(value)
                    self.play.setText('▶  Resume' if value else ('Ⅱ  Pause' if self.current else '▶  Play'))
                    if self.current: self.status.setText('Paused' if value else 'Playing')
                elif prop == 'paused-for-cache' and value:
                    self.status.setText('Buffering…')

    def closeEvent(self, event):
        self.retry.stop()
        self.command('quit')
        if not self.process.waitForFinished(1200):
            self.process.terminate()
            if not self.process.waitForFinished(800):
                self.process.kill()
                self.process.waitForFinished(500)
        self.socket.abort()
        self.temp.cleanup()
        event.accept()

STYLE = '''
QWidget { background:#121c1d; color:#dce5df; font-family:"DejaVu Sans"; font-size:13px; }
QLabel { background:transparent; }
QLabel#brand {font-size:30px; font-weight:800; letter-spacing:-1px;}
QLabel#station {font-size:36px; font-weight:700; color:#f2f2df;}
QLabel#badge {color:#b7eb93; font-size:11px; font-weight:700;}
QLabel#footer {color:#839994; font-size:11px;}
QFrame#card {background:#1c2b2c; border:1px solid #344647; border-radius:18px;}
QListWidget {background:#121c1d; border:none; outline:none;}
QListWidget::item {padding:18px 12px; border-radius:9px; margin-bottom:7px; background:#1a2728;}
QListWidget::item:selected {background:#344738; color:#d7f7bd;}
QListWidget::item:hover {background:#263737;}
QLineEdit {padding:12px; border:1px solid #344647; border-radius:8px; background:#1a2728;}
QPushButton {padding:12px 15px; border:1px solid #3a4b49; border-radius:9px; background:#223131;}
QPushButton:hover {background:#344a43; border-color:#b7eb93;}
QPushButton:disabled {color:#61716b;}
QPushButton#play {background:#b7eb93; color:#19271b; font-weight:700; border:none;}
QSlider::groove:horizontal {height:5px; background:#344647; border-radius:2px;}
QSlider::sub-page:horizontal {background:#b7eb93; border-radius:2px;}
QSlider::handle:horizontal {background:#d7f7bd; width:15px; margin:-5px 0; border-radius:7px;}
'''

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('Airwave')
    app.setDesktopFileName('airwave')
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    if not shutil.which('mpv'):
        QMessageBox.critical(None, 'Missing mpv', 'Install mpv to use Airwave.')
        sys.exit(1)
    window = Player()
    window.show()
    sys.exit(app.exec())
