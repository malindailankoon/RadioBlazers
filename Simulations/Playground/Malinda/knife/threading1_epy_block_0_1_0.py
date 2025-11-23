#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gnuradio import gr
from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import pmt
import time
from datetime import datetime  # for timestamps

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


class messenger_gui(gr.basic_block):
    """
    WhatsApp-style Messenger GUI with dynamic bubble resizing,
    horizontal scroll for long messages, timestamp update on delivery,
    and failure indication if retry limit is exceeded.
    """

    def __init__(self, bg_image=""):
        gr.basic_block.__init__(
            self,
            name="Messenger GUI",
            in_sig=None,
            out_sig=None,
        )

        # Message ports
        self.message_port_register_out(pmt.intern("out"))
        self.message_port_register_in(pmt.intern("feedback"))
        self.set_msg_handler(pmt.intern("feedback"), self._process_feedback)

        # Qt Application
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication(sys.argv)

        self.qt_widget = QtWidgets.QWidget()
        self.qt_widget.setWindowTitle("Messenger GUI")
        self.qt_widget.resize(600, 500)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.qt_widget.setLayout(main_layout)

        # Scroll area with background
        self.scroll_area = WallpaperScrollArea(bg_image=bg_image)
        self.scroll_area.setStyleSheet("border: none;")
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # Chat container
        self.chat_container = QtWidgets.QWidget()
        self.chat_layout = QtWidgets.QVBoxLayout()
        self.chat_layout.setAlignment(QtCore.Qt.AlignTop)
        self.chat_layout.setSpacing(10)
        self.chat_container.setLayout(self.chat_layout)
        self.chat_container.setStyleSheet("background: transparent;")
        self.scroll_area.setWidget(self.chat_container)

        # Input area
        input_layout = QtWidgets.QHBoxLayout()
        self.input_box = QtWidgets.QLineEdit()
        self.input_box.setPlaceholderText("Type a message...")
        self.input_box.setStyleSheet("""
            QLineEdit {
                border-radius: 15px;
                padding: 12px;
                background-color: rgba(255,255,255,230);
                font-size: 32px;
            }
        """)
        self.send_button = QtWidgets.QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 15px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 32px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_button)
        main_layout.addLayout(input_layout)

        # Connect signals
        self.send_button.clicked.connect(self.send_message)
        self.input_box.returnPressed.connect(self.send_message)

        self._last_message_timestamp = None
        self.qt_widget.show()

    def send_message(self):
        text = self.input_box.text().strip()
        if not text:
            return

        # Send message via GNU Radio port
        self.message_port_pub(pmt.intern("out"), pmt.string_to_symbol(text))

        # Scrollable bubble container
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background: transparent;")

        # Message bubble
        bubble = QtWidgets.QLabel(text)
        bubble.setWordWrap(False)  # Disable wrapping
        bubble.setStyleSheet("""
            QLabel {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4CAF50, stop:1 #66BB6A);
                color: white;
                border-radius: 15px;
                padding: 10px 15px;
                font-size: 32px;
            }
        """)

        # Shadow effect
        effect = QtWidgets.QGraphicsDropShadowEffect()
        effect.setBlurRadius(6)
        effect.setXOffset(2)
        effect.setYOffset(2)
        effect.setColor(QtGui.QColor(0, 0, 0, 100))
        bubble.setGraphicsEffect(effect)

        scroll.setWidget(bubble)
        scroll.setMinimumWidth(200)
        scroll.setMaximumWidth(550)  # Max visible width of bubble
        bubble.adjustSize()
        scroll.adjustSize()

        # Timestamp label as small blue pill initially
        timestamp = QtWidgets.QLabel("Sending...")
        timestamp.setStyleSheet("""
            QLabel {
                background-color: #2196F3;  /* blue background */
                color: white;
                font-size: 18px;
                border-radius: 8px;
                padding: 2px 6px;
            }
        """)
        timestamp.setAlignment(QtCore.Qt.AlignRight)
        timestamp.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        # Container for bubble + timestamp
        container = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)
        vbox.addWidget(scroll)
        vbox.addWidget(timestamp, alignment=QtCore.Qt.AlignRight)
        container.setLayout(vbox)
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # Add to chat layout
        self.chat_layout.addWidget(container, alignment=QtCore.Qt.AlignRight)

        # Force proper size recalculation
        bubble.adjustSize()
        scroll.adjustSize()
        container.adjustSize()
        self.chat_container.adjustSize()
        QtWidgets.QApplication.processEvents()  # Force layout update

        # Scroll to bottom
        QtCore.QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

        self.input_box.clear()
        self._last_message_timestamp = timestamp

    def _process_feedback(self, msg):
        try:
            if pmt.is_symbol(msg):
                feedback = pmt.symbol_to_string(msg)

                if feedback == "END_ACK_RECEIVED" and self._last_message_timestamp:
                    # Successful delivery: show current time in blue pill
                    self._last_message_timestamp.setText(datetime.now().strftime("%H:%M"))
                    self._last_message_timestamp.setStyleSheet("""
                        QLabel {
                            background-color: #2196F3;  /* blue background */
                            color: white;
                            font-size: 18px;
                            border-radius: 8px;
                            padding: 2px 6px;
                        }
                    """)

                elif feedback == "RETRY_LIMIT_EXCEEDED" and self._last_message_timestamp:
                    # Failed delivery: red pill
                    self._last_message_timestamp.setText("Failed")
                    self._last_message_timestamp.setStyleSheet("""
                        QLabel {
                            background-color: #F44336;  /* red background */
                            color: white;
                            font-size: 18px;
                            border-radius: 8px;
                            padding: 2px 6px;
                        }
                    """)

        except Exception as e:
            print(f"[messenger_gui] Error processing feedback: {e}")

