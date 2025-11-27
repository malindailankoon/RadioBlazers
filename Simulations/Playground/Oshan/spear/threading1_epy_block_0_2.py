#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gnuradio import gr
from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import pmt
from datetime import datetime

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


class _GuiPoster(QtCore.QObject):
    """Helper QObject to post strings into the Qt thread safely."""
    sig = QtCore.pyqtSignal(str)  # emits text payload

    def __init__(self):
        super().__init__()


class messenger_gui(gr.basic_block):
    """
    WhatsApp-style Messenger GUI (GNU Radio embedded block).
    - Outgoing messages: published on message port "out" with address prepended as "addr:body"
    - Feedback port "feedback": updates delivery timestamp / failed status
    - Incoming messages: received on port "in_msg" (same format "addr:body") and displayed
      on the left in a different color.
    """

    def __init__(self, bg_image=""):
        gr.basic_block.__init__(
            self,
            name="Messenger GUI",
            in_sig=None,
            out_sig=None,
        )

        # Message ports
        self.message_port_register_out(pmt.intern("out"))    # outgoing messages
        self.message_port_register_in(pmt.intern("feedback"))# delivery feedback
        self.message_port_register_in(pmt.intern("in_msg"))  # incoming messages from remote/devices

        # Bind handlers
        self.set_msg_handler(pmt.intern("feedback"), self._process_feedback)
        self.set_msg_handler(pmt.intern("in_msg"), self._receive_message)

        # Poster used to safely move messages to GUI thread
        self._poster = _GuiPoster()
        self._poster.sig.connect(self._display_incoming)  # connect to GUI-thread handler

        # Qt Application
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication(sys.argv)

        # Main window
        self.qt_widget = QtWidgets.QWidget()
        self.qt_widget.setWindowTitle("Messenger GUI")
        self.qt_widget.resize(640, 560)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        self.qt_widget.setLayout(main_layout)

        # Address selection bar
        addr_layout = QtWidgets.QHBoxLayout()
        addr_label = QtWidgets.QLabel("To:")
        addr_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        addr_layout.addWidget(addr_label)

        self.addr_box = QtWidgets.QComboBox()
        self.addr_box.addItems([str(i) for i in range(1, 11)])  # 1..10 default
        self.addr_box.setFixedWidth(100)
        self.addr_box.setStyleSheet("font-size: 16px; padding: 4px;")
        addr_layout.addWidget(self.addr_box)
        addr_layout.addStretch()

        main_layout.addLayout(addr_layout)

        # Scroll area with background
        self.scroll_area = WallpaperScrollArea(bg_image=bg_image)
        self.scroll_area.setStyleSheet("border: none;")
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # Chat container (vertical list of message widgets)
        self.chat_container = QtWidgets.QWidget()
        self.chat_layout = QtWidgets.QVBoxLayout()
        self.chat_layout.setAlignment(QtCore.Qt.AlignTop)
        self.chat_layout.setSpacing(10)
        self.chat_container.setLayout(self.chat_layout)
        self.chat_container.setStyleSheet("background: transparent;")
        self.scroll_area.setWidget(self.chat_container)

        # Input area (text entry + send)
        input_layout = QtWidgets.QHBoxLayout()
        self.input_box = QtWidgets.QLineEdit()
        self.input_box.setPlaceholderText("Type a message...")
        self.input_box.setMinimumHeight(40)
        self.input_box.setStyleSheet("""
            QLineEdit {
                border-radius: 12px;
                padding: 8px;
                background-color: rgba(255,255,255,0.95);
                font-size: 16px;
            }
        """)
        self.send_button = QtWidgets.QPushButton("Send")
        self.send_button.setMinimumHeight(40)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        input_layout.addWidget(self.input_box, stretch=1)
        input_layout.addWidget(self.send_button, stretch=0)
        main_layout.addLayout(input_layout)

        # Connect GUI signals
        self.send_button.clicked.connect(self.send_message)
        self.input_box.returnPressed.connect(self.send_message)

        # Track last sent message timestamp widget (simple approach)
        # If you want per-message tracking, change to a list/map of widgets per message id.
        self._last_message_timestamp = None

        # show window
        self.qt_widget.show()

    def send_message(self):
        """Called from GUI thread when user presses Send or Enter."""
        text = self.input_box.text().strip()
        if not text:
            return

        addr = self.addr_box.currentText().strip()
        full_msg = f"{addr}:{text}"

        # Publish as PMT symbol/string on 'out' port
        try:
            self.message_port_pub(pmt.intern("out"), pmt.intern(full_msg))
        except Exception:
            # fallback to generic intern
            self.message_port_pub(pmt.intern("out"), pmt.intern(full_msg))

        # Build outgoing bubble (right side)
        container = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)

        # Scrollable area for long messages
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        bubble = QtWidgets.QLabel(text)  # show only body (user-friendly)
        bubble.setWordWrap(False)
        bubble.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        bubble.setStyleSheet("""
            QLabel {
                background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #4CAF50, stop:1 #66BB6A);
                color: white;
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 14px;
            }
        """)
        # shadow
        effect = QtWidgets.QGraphicsDropShadowEffect()
        effect.setBlurRadius(6)
        effect.setXOffset(2)
        effect.setYOffset(2)
        effect.setColor(QtGui.QColor(0, 0, 0, 80))
        bubble.setGraphicsEffect(effect)

        scroll.setWidget(bubble)
        scroll.setMinimumWidth(160)
        scroll.setMaximumWidth(520)

        # Timestamp pill (initially 'Sending...')
        timestamp = QtWidgets.QLabel("Sending...")
        timestamp.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                font-size: 11px;
                border-radius: 8px;
                padding: 2px 6px;
            }
        """)
        timestamp.setAlignment(QtCore.Qt.AlignRight)
        timestamp.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        vbox.addWidget(scroll, alignment=QtCore.Qt.AlignRight)
        vbox.addWidget(timestamp, alignment=QtCore.Qt.AlignRight)
        container.setLayout(vbox)
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # Add to chat layout (right aligned)
        self.chat_layout.addWidget(container, alignment=QtCore.Qt.AlignRight)

        # Force layout update and scroll to bottom
        bubble.adjustSize()
        scroll.adjustSize()
        container.adjustSize()
        self.chat_container.adjustSize()
        QtWidgets.QApplication.processEvents()
        QtCore.QTimer.singleShot(20, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

        # Clear input and store timestamp widget for feedback updates
        self.input_box.clear()
        self._last_message_timestamp = timestamp

    def _process_feedback(self, msg_pmt):
        """
        Handler for 'feedback' port. Expected feedback values:
          - "TRUE" => show delivery time
          - "FALSE" => show 'Failed'
        """
        try:
            if pmt.is_symbol(msg_pmt) or pmt.is_string(msg_pmt):
                fb = pmt.symbol_to_string(msg_pmt)
            else:
                py = pmt.to_python(msg_pmt)
                fb = str(py)
        except Exception:
            fb = "<unreadable feedback>"

        print(fb)
        # Update last timestamp widget if available (simple single-last approach)
        if self._last_message_timestamp:
            if fb == "TRUE":
                self._last_message_timestamp.setText(datetime.now().strftime("%H:%M:%S"))
                self._last_message_timestamp.setStyleSheet("""
                    QLabel {
                        background-color: #2196F3;
                        color: white;
                        font-size: 11px;
                        border-radius: 8px;
                        padding: 2px 6px;
                    }
                """)
            elif fb == "FALSE":
                self._last_message_timestamp.setText("Failed")
                self._last_message_timestamp.setStyleSheet("""
                    QLabel {
                        background-color: #F44336;
                        color: white;
                        font-size: 11px;
                        border-radius: 8px;
                        padding: 2px 6px;
                    }
                """)

    def _receive_message(self, msg_pmt):
        """
        Handler for 'in_msg' port. Extracts string and posts it to GUI thread
        via _poster.sig so _display_incoming runs in Qt thread.
        """
        try:
            if pmt.is_symbol(msg_pmt) or pmt.is_string(msg_pmt):
                s = pmt.symbol_to_string(msg_pmt)
            else:
                py = pmt.to_python(msg_pmt)
                s = str(py)
        except Exception:
            s = "<unreadable message>"

        # Post to GUI-thread handler
        try:
            self._poster.sig.emit(s)
        except Exception:
            # If signal emit fails for any reason, try direct call in case we're already in Qt thread
            try:
                self._display_incoming(s)
            except Exception:
                print("[messenger_gui] failed to deliver incoming message to GUI:", s)

    def _display_incoming(self, full_msg):
        """
        Build incoming bubble (left aligned). full_msg expected in "addr:body" format.
        """
        # try to split "addr:body"
        if ":" in full_msg:
            addr, body = full_msg.split(":", 1)
            display_text = f"{body}"
            header_text = f"{addr}"
        else:
            display_text = full_msg
            header_text = ""

        container = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        bubble = QtWidgets.QLabel(display_text)
        bubble.setWordWrap(False)
        bubble.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        bubble.setStyleSheet("""
            QLabel {
                background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #E1F5FE, stop:1 #B3E5FC);
                color: #0B2545;
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 14px;
            }
        """)

        # small header with sender address (optional)
        if header_text:
            header = QtWidgets.QLabel(header_text)
            header.setStyleSheet("font-size: 11px; color: #1565C0;")
            header.setAlignment(QtCore.Qt.AlignLeft)
            vbox.addWidget(header, alignment=QtCore.Qt.AlignLeft)

        scroll.setWidget(bubble)
        scroll.setMinimumWidth(160)
        scroll.setMaximumWidth(520)

        vbox.addWidget(scroll, alignment=QtCore.Qt.AlignLeft)

        # incoming messages do not have delivery timestamp pill (feedback relates to outgoing)
        container.setLayout(vbox)
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.chat_layout.addWidget(container, alignment=QtCore.Qt.AlignLeft)

        # Update layout and scroll to bottom
        bubble.adjustSize()
        scroll.adjustSize()
        container.adjustSize()
        self.chat_container.adjustSize()
        QtWidgets.QApplication.processEvents()
        QtCore.QTimer.singleShot(20, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
