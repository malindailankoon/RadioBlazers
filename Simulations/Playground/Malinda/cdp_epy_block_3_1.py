#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gnuradio import gr
from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import pmt
from datetime import datetime  # For timestamps

class WallpaperScrollArea(QtWidgets.QScrollArea):
    def __init__(self, bg_image="", parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.bg_pixmap = QtGui.QPixmap(bg_image) if bg_image else None

    def paintEvent(self, event):
        if self.bg_pixmap:
            painter = QtGui.QPainter(self.viewport())
            painter.drawPixmap(self.viewport().rect(), self.bg_pixmap)
        super().paintEvent(event)

class multi_sender_gui(gr.basic_block):
    """
    Multi-sender PDU GUI with dark bluish-grey left panel
    and Messenger-style scalable chat bubbles with timestamps.
    """

    def __init__(self, bg_image=""):
        gr.basic_block.__init__(self,
            name="Multi-Sender PDU Viewer",
            in_sig=None,
            out_sig=None
        )

        self.bg_image = bg_image
        self.msg_queue = []
        self.sender_msgs = {}
        self.sender_buttons = {}
        self.current_sender = None
        self.unread = set()

        # PDU input
        self.message_port_register_in(pmt.intern("in"))
        self.set_msg_handler(pmt.intern("in"), self.handle_pdu)

        # Ensure QApplication exists
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication(sys.argv)

        # Initialize GUI
        self.init_gui()

    def init_gui(self):
        self.qt_widget = QtWidgets.QWidget()
        self.qt_widget.setWindowTitle("Multi-Sender PDU Viewer")
        self.qt_widget.resize(800, 500)

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        self.qt_widget.setLayout(main_layout)

        # Left: sender panel
        self.sender_layout_widget = QtWidgets.QWidget()
        self.sender_layout_widget.setStyleSheet("background-color: #1B263B;")
        self.sender_layout = QtWidgets.QVBoxLayout()
        self.sender_layout.setAlignment(QtCore.Qt.AlignTop)
        self.sender_layout_widget.setLayout(self.sender_layout)
        main_layout.addWidget(self.sender_layout_widget)
        self.sender_layout_widget.setFixedWidth(150)

        # Right: chat with wallpaper
        self.scroll_area = WallpaperScrollArea(bg_image=self.bg_image)
        self.scroll_area.setWidgetResizable(True)
        self.chat_container = QtWidgets.QWidget()
        self.chat_layout = QtWidgets.QVBoxLayout()
        self.chat_layout.setAlignment(QtCore.Qt.AlignTop)
        self.chat_container.setLayout(self.chat_layout)
        self.chat_container.setStyleSheet("background: transparent;")
        self.scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # Show widget
        self.qt_widget.show()

        # Timer to process incoming messages
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.process_queue)
        self.timer.start(50)

    def handle_pdu(self, msg):
        self.msg_queue.append(msg)

    def process_queue(self):
        while self.msg_queue:
            msg = self.msg_queue.pop(0)
            self.store_message(msg)

    def store_message(self, msg):
        if not pmt.is_pair(msg):
            return
        vec = pmt.cdr(msg)
        if not pmt.is_u8vector(vec):
            return

        data = bytearray(pmt.u8vector_elements(vec))
        if len(data) < 1:
            return

        sender_bytes = data[0:1]
        sender = f"Node {sender_bytes[0]:02X}"
        payload = data[1:]

        try:
            text = payload.decode("utf-8", errors="ignore")
        except Exception:
            text = "<decode error>"

        if sender not in self.sender_msgs:
            self.sender_msgs[sender] = []
            self.add_sender_slot(sender)
        self.sender_msgs[sender].append(text)

        if self.current_sender != sender:
            self.unread.add(sender)
            self.update_sender_slot(sender)

        if self.current_sender == sender or self.current_sender is None:
            self.display_sender_messages(sender)

    def add_sender_slot(self, sender):
        slot_widget = QtWidgets.QWidget()
        slot_widget.setFixedHeight(50)
        slot_widget.setStyleSheet("""
            background-color: #2C3E50;
            border-radius: 8px;
        """)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(10,0,10,0)
        slot_widget.setLayout(layout)

        name_label = QtWidgets.QLabel(sender)
        name_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(name_label, alignment=QtCore.Qt.AlignLeft)

        dot_label = QtWidgets.QLabel("\u25CF")
        dot_label.setStyleSheet("color: yellow; font-weight: bold;")
        dot_label.setVisible(False)
        layout.addWidget(dot_label, alignment=QtCore.Qt.AlignRight)

        slot_widget.mousePressEvent = lambda e, s=sender: self.display_sender_messages(s)

        self.sender_buttons[sender] = {'widget': slot_widget, 'dot': dot_label, 'name': name_label}
        self.sender_layout.addWidget(slot_widget)

    def update_sender_slot(self, sender):
        btn_info = self.sender_buttons.get(sender)
        if btn_info:
            btn_info['dot'].setVisible(sender in self.unread)

    def display_sender_messages(self, sender):
        self.current_sender = sender
        if sender in self.unread:
            self.unread.remove(sender)
            self.update_sender_slot(sender)

        # Clear chat layout
        for i in reversed(range(self.chat_layout.count())):
            w = self.chat_layout.takeAt(i).widget()
            if w:
                w.deleteLater()

        msgs = self.sender_msgs.get(sender, [])
        for text in msgs:
            self.add_bubble(text)

        QtCore.QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def add_bubble(self, text):
        # Chat bubble
        bubble = QtWidgets.QLabel(text)
        bubble.setWordWrap(True)
        bubble.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                border-radius: 15px;
                padding: 20px 30px;
                font-size: 32px;
            }
        """)
        bubble.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        bubble.setMaximumWidth(500)
        bubble.setMinimumHeight(bubble.sizeHint().height())

        # Shadow effect
        effect = QtWidgets.QGraphicsDropShadowEffect()
        effect.setBlurRadius(6)
        effect.setXOffset(2)
        effect.setYOffset(2)
        effect.setColor(QtGui.QColor(0,0,0,100))
        bubble.setGraphicsEffect(effect)

        # Timestamp with small green "pill"
        timestamp = QtWidgets.QLabel(datetime.now().strftime("%H:%M"))
        timestamp.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;  /* green background */
                color: white;
                font-size: 18px;
                border-radius: 8px;
                padding: 2px 6px;
            }
        """)
        timestamp.setAlignment(QtCore.Qt.AlignRight)
        timestamp.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)  # <-- small pill only

        # Container for bubble + timestamp
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignLeft)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(bubble)
        layout.addWidget(timestamp, alignment=QtCore.Qt.AlignRight)  # timestamp right-aligned
        container.setLayout(layout)

        self.chat_layout.addWidget(container, alignment=QtCore.Qt.AlignLeft)

# Run GUI for standalone testing
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    gui = multi_sender_gui()
    sys.exit(app.app.exec_())

