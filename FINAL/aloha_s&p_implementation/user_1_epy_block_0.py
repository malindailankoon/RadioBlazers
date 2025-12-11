#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gnuradio import gr
from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import pmt
from datetime import datetime
import os

# For sound effects
try:
    import pygame
    pygame.mixer.init()
    SOUND_ENABLED = True
except:
    SOUND_ENABLED = False
    print("Sound disabled: pygame not installed")

class WallpaperScrollArea(QtWidgets.QScrollArea):
    def __init__(self, bg_image="", parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        # Hospital-themed background gradient
        self.bg_color1 = QtGui.QColor(240, 248, 255)  # Alice Blue
        self.bg_color2 = QtGui.QColor(230, 240, 255)  # Lighter blue
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self.viewport())
        
        # Draw gradient background
        gradient = QtGui.QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, self.bg_color1)
        gradient.setColorAt(1, self.bg_color2)
        painter.fillRect(self.rect(), gradient)
        
        # Draw subtle grid lines (like hospital forms)
        painter.setPen(QtGui.QPen(QtGui.QColor(220, 230, 240), 1))
        for i in range(0, self.height(), 20):
            painter.drawLine(0, i, self.width(), i)
        
        super().paintEvent(event)


class AnimatedButton(QtWidgets.QPushButton):
    """Button with smooth animation for hospital theme"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.animation = QtCore.QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(150)
        self.default_style = ""
        
    def enterEvent(self, event):
        self.animation.stop()
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(QtCore.QRect(
            self.x() - 1, self.y() - 1,
            self.width() + 2, self.height() + 2
        ))
        self.animation.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.animation.stop()
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(QtCore.QRect(
            self.x() + 1, self.y() + 1,
            self.width() - 2, self.height() - 2
        ))
        self.animation.start()
        super().leaveEvent(event)


class CharacterCounter(QtWidgets.QLabel):
    """Character counter widget that changes color based on remaining characters"""
    def __init__(self, max_chars=255, parent=None):
        super().__init__(parent)
        self.max_chars = max_chars
        self.current_chars = 0
        self.update_display()
        
    def update_count(self, text):
        """Update the counter with new text length"""
        self.current_chars = len(text)
        self.update_display()
        
    def update_display(self):
        """Update the display with current count and appropriate color"""
        remaining = self.max_chars - self.current_chars
        percentage = (self.current_chars / self.max_chars) * 100
        
        # Set text
        self.setText(f"{self.current_chars}/{self.max_chars}")
        
        # Change color based on remaining characters
        if remaining < 0:
            # Over limit - red
            self.setStyleSheet("""
                QLabel {
                    color: #E53E3E;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
        elif remaining <= 25:  # Less than 25 characters left
            # Warning - orange
            self.setStyleSheet("""
                QLabel {
                    color: #D69E2E;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
        elif percentage >= 75:  # Over 75% used
            # Caution - yellow
            self.setStyleSheet("""
                QLabel {
                    color: #ECC94B;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
        else:
            # Normal - green/blue
            self.setStyleSheet("""
                QLabel {
                    color: #38A169;
                    font-weight: bold;
                    font-size: 12px;
                }
            """)
            
    def is_valid(self):
        """Check if current text length is within limit"""
        return self.current_chars <= self.max_chars and self.current_chars > 0


class MessageBubble(QtWidgets.QFrame):
    """Individual message bubble for hospital paging system"""
    def __init__(self, text, is_outgoing=True, address="", numeric_address="", parent=None):
        super().__init__(parent)
        self.is_outgoing = is_outgoing
        self.address = address  # Display address (e.g., "Station 1")
        self.numeric_address = numeric_address  # Actual numeric address (e.g., "1")
        
        self.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.setFixedWidth(400)
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(4)
        
        # Header with address and time
        header_layout = QtWidgets.QHBoxLayout()
        
        if is_outgoing:
            header_label = QtWidgets.QLabel(f"TO: {address}")
            header_label.setStyleSheet("""
                QLabel {
                    color: #2C5282;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)
            header_layout.addWidget(header_label, alignment=QtCore.Qt.AlignRight)
        else:
            header_label = QtWidgets.QLabel(f"FROM: {address}")
            header_label.setStyleSheet("""
                QLabel {
                    color: #234E52;
                    font-weight: bold;
                    font-size: 11px;
                }
            """)
            header_layout.addWidget(header_label, alignment=QtCore.Qt.AlignLeft)
        
        time_label = QtWidgets.QLabel(datetime.now().strftime("%H:%M"))
        time_label.setStyleSheet("""
            QLabel {
                color: #718096;
                font-size: 10px;
            }
        """)
        header_layout.addWidget(time_label, alignment=QtCore.Qt.AlignRight if is_outgoing else QtCore.Qt.AlignLeft)
        main_layout.addLayout(header_layout)
        
        # Message text
        text_label = QtWidgets.QLabel(text)
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        
        if is_outgoing:
            # Outgoing: doctor/nurse sending
            self.setStyleSheet("""
                MessageBubble {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #BEE3F8, stop:1 #90CDF4);
                    border: 2px solid #4299E1;
                    border-radius: 8px;
                }
            """)
            text_label.setStyleSheet("""
                QLabel {
                    color: #2D3748;
                    font-size: 13px;
                    font-weight: 500;
                    padding: 8px;
                }
            """)
        else:
            # Incoming: patient/other staff
            self.setStyleSheet("""
                MessageBubble {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #F0FFF4, stop:1 #C6F6D5);
                    border: 2px solid #48BB78;
                    border-radius: 8px;
                }
            """)
            text_label.setStyleSheet("""
                QLabel {
                    color: #22543D;
                    font-size: 13px;
                    font-weight: 500;
                    padding: 8px;
                }
            """)
        
        main_layout.addWidget(text_label)
        
        # Status indicator (only for outgoing messages)
        if is_outgoing:
            self.status_label = QtWidgets.QLabel("⏳ Sending...")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #D69E2E;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            main_layout.addWidget(self.status_label, alignment=QtCore.Qt.AlignRight)
        
        # Small label showing actual numeric address (subtle, for debugging)
        if numeric_address and numeric_address != address:
            numeric_label = QtWidgets.QLabel(f"[ID: {numeric_address}]")
            numeric_label.setStyleSheet("""
                QLabel {
                    color: #A0AEC0;
                    font-size: 9px;
                    font-style: italic;
                }
            """)
            if is_outgoing:
                main_layout.addWidget(numeric_label, alignment=QtCore.Qt.AlignRight)
            else:
                main_layout.addWidget(numeric_label, alignment=QtCore.Qt.AlignLeft)
        
        # Animation for new messages
        self.fade_animation = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()


class _GuiPoster(QtCore.QObject):
    """Helper QObject to post strings into the Qt thread safely."""
    sig = QtCore.pyqtSignal(str)  # emits text payload

    def __init__(self):
        super().__init__()


class messenger_gui(gr.basic_block):
    """
    Hospital Paging System GUI (GNU Radio embedded block).
    - Outgoing messages: published on message port "out" with numeric address prepended as "addr:body"
    - Feedback port "feedback": updates delivery status
    - Incoming messages: received on port "in_msg" (same numeric format "addr:body")
    """

    def __init__(self, bg_image=""):
        gr.basic_block.__init__(
            self,
            name="Hospital Paging System",
            in_sig=None,
            out_sig=None,
        )

        # Message ports
        self.message_port_register_out(pmt.intern("out"))    # outgoing messages
        self.message_port_register_out(pmt.intern("sync_cmd"))
        self.message_port_register_in(pmt.intern("feedback"))# delivery feedback
        self.message_port_register_in(pmt.intern("in_msg"))  # incoming messages from remote/devices

        # Bind handlers
        self.set_msg_handler(pmt.intern("feedback"), self._process_feedback)
        self.set_msg_handler(pmt.intern("in_msg"), self._receive_message)

        # Poster used to safely move messages to GUI thread
        self._poster = _GuiPoster()
        self._poster.sig.connect(self._display_incoming)  # connect to GUI-thread handler

        # Message tracking
        self.message_widgets = {}  # Store message widgets for feedback
        self.message_counter = 0
        self.MAX_CHARS = 255  # Maximum characters allowed

        # Qt Application
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication(sys.argv)

        # Set hospital-like font
        font = QtGui.QFont("Arial", 10)
        self.app.setFont(font)

        # Main window
        self.qt_widget = QtWidgets.QWidget()
        self.qt_widget.setWindowTitle("🏥 Hospital Paging System - Station 1")
        self.qt_widget.resize(1000, 800)
        self.qt_widget.setStyleSheet("""
            QWidget {
                background-color: #F7FAFC;
            }
        """)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        self.qt_widget.setLayout(main_layout)

        # Title Bar
        title_layout = QtWidgets.QHBoxLayout()
        
        # Hospital logo/icon
        icon_label = QtWidgets.QLabel("🏥")
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
            }
        """)
        title_layout.addWidget(icon_label)
        
        title_label = QtWidgets.QLabel("HOSPITAL PAGING SYSTEM")
        title_label.setStyleSheet("""
            QLabel {
                color: #2C5282;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Arial Black';
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # System status
        status_label = QtWidgets.QLabel("🟢 ONLINE")
        status_label.setStyleSheet("""
            QLabel {
                color: #38A169;
                font-size: 14px;
                font-weight: bold;
                background-color: #C6F6D5;
                padding: 4px 12px;
                border-radius: 12px;
                border: 1px solid #38A169;
            }
        """)
        title_layout.addWidget(status_label)
        
        main_layout.addLayout(title_layout)

        # Control Panel
        control_frame = QtWidgets.QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background-color: #EDF2F7;
                border: 2px solid #CBD5E0;
                border-radius: 10px;
            }
        """)
        control_frame.setFixedHeight(150)
        
        control_layout = QtWidgets.QHBoxLayout(control_frame)
        control_layout.setContentsMargins(20, 15, 20, 15)
        
        # Recipient Selection - GUI shows "Station X" but uses numeric address internally
        recipient_group = QtWidgets.QGroupBox("PAGE RECIPIENT")
        recipient_group.setStyleSheet("""
            QGroupBox {
                color: #4A5568;
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #A0AEC0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        recipient_layout = QtWidgets.QHBoxLayout(recipient_group)
        
        # Create stations 1-10 for display, but we'll use numeric addresses
        self.addr_box = QtWidgets.QComboBox()
        # Add stations 1-10 with display names
        for i in range(1, 11):
            self.addr_box.addItem(f"Station {i}", userData=str(i))  # Display: "Station 1", Data: "1"
        
        # Add some special stations with their numeric IDs
        self.addr_box.addItem("Emergency Room", userData="11")
        self.addr_box.addItem("Pharmacy", userData="12")
        self.addr_box.addItem("Lab", userData="13")
        self.addr_box.addItem("Radiology", userData="14")
        
        self.addr_box.setFixedWidth(180)
        self.addr_box.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 2px solid #4299E1;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QComboBox:hover {
                border-color: #3182CE;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        recipient_layout.addWidget(self.addr_box)
        control_layout.addWidget(recipient_group)

        control_layout.addSpacing(20)

        # Message Input with character counter
        input_group = QtWidgets.QGroupBox("MESSAGE")
        input_group.setStyleSheet("""
            QGroupBox {
                color: #4A5568;
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #A0AEC0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        input_layout = QtWidgets.QVBoxLayout(input_group)
        
        # Character counter at the top
        counter_layout = QtWidgets.QHBoxLayout()
        counter_label = QtWidgets.QLabel("Characters:")
        counter_label.setStyleSheet("""
            QLabel {
                color: #4A5568;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        counter_layout.addWidget(counter_label)
        
        self.char_counter = CharacterCounter(max_chars=self.MAX_CHARS)
        counter_layout.addWidget(self.char_counter)
        counter_layout.addStretch()
        
        # Add limit info
        limit_label = QtWidgets.QLabel(f"(Max: {self.MAX_CHARS} characters)")
        limit_label.setStyleSheet("""
            QLabel {
                color: #718096;
                font-size: 10px;
                font-style: italic;
            }
        """)
        counter_layout.addWidget(limit_label)
        input_layout.addLayout(counter_layout)
        
        # Message input box
        input_box_layout = QtWidgets.QHBoxLayout()
        self.input_box = QtWidgets.QLineEdit()
        self.input_box.setPlaceholderText(f"Type your message here (max {self.MAX_CHARS} characters)...")
        self.input_box.setFixedHeight(40)
        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #CBD5E0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4299E1;
            }
            QLineEdit[invalid="true"] {
                border-color: #E53E3E;
                background-color: #FFF5F5;
            }
        """)
        self.input_box.textChanged.connect(self.update_character_counter)
        input_box_layout.addWidget(self.input_box)
        input_layout.addLayout(input_box_layout)
        
        control_layout.addWidget(input_group)

        control_layout.addSpacing(20)

        # Action Buttons
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setSpacing(10)
        
        self.send_button = AnimatedButton("📤 SEND PAGE")
        self.send_button.setFixedSize(120, 40)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4299E1, stop:1 #3182CE);
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3182CE, stop:1 #2B6CB0);
            }
            QPushButton:pressed {
                background-color: #2C5282;
            }
            QPushButton:disabled {
                background-color: #CBD5E0;
                color: #718096;
            }
        """)
        
        self.sync_button = AnimatedButton("🔄 SYNC")
        self.sync_button.setFixedSize(120, 40)
        self.sync_button.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #38A169, stop:1 #2F855A);
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2F855A, stop:1 #276749);
            }
            QPushButton:pressed {
                background-color: #22543D;
            }
        """)
        
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.sync_button)
        control_layout.addLayout(button_layout)
        
        main_layout.addWidget(control_frame)

        # Messages Display Area
        messages_frame = QtWidgets.QFrame()
        messages_frame.setStyleSheet("""
            QFrame {
                background-color: #F7FAFC;
                border: 2px solid #CBD5E0;
                border-radius: 10px;
            }
        """)
        
        messages_layout = QtWidgets.QVBoxLayout(messages_frame)
        messages_layout.setContentsMargins(15, 15, 15, 15)
        
        # Messages header
        messages_header = QtWidgets.QLabel("📨 MESSAGE LOG")
        messages_header.setStyleSheet("""
            QLabel {
                color: #4A5568;
                font-size: 16px;
                font-weight: bold;
                padding-bottom: 10px;
                border-bottom: 2px solid #E2E8F0;
            }
        """)
        messages_layout.addWidget(messages_header)
        
        # Scroll area for messages
        self.scroll_area = WallpaperScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        # Chat container
        self.chat_container = QtWidgets.QWidget()
        self.chat_layout = QtWidgets.QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(QtCore.Qt.AlignTop)
        self.chat_layout.setSpacing(12)
        self.chat_container.setLayout(self.chat_layout)
        self.scroll_area.setWidget(self.chat_container)
        
        messages_layout.addWidget(self.scroll_area)
        main_layout.addWidget(messages_frame, stretch=1)

        # Footer
        footer_layout = QtWidgets.QHBoxLayout()
        footer_label = QtWidgets.QLabel("© RadioBlazers | EN2130 Communication Design Project | Hospital Paging System")
        footer_label.setStyleSheet("""
            QLabel {
                color: #718096;
                font-size: 11px;
                font-style: italic;
            }
        """)
        footer_layout.addWidget(footer_label)
        main_layout.addLayout(footer_layout)

        # Connect GUI signals
        self.send_button.clicked.connect(self.send_message)
        self.input_box.returnPressed.connect(self.send_message)
        self.sync_button.clicked.connect(self.send_sync_cmd)
        
        # Initial button state
        self.update_send_button_state()

        # Show window
        self.qt_widget.show()
        
    def update_character_counter(self):
        """Update the character counter when text changes"""
        text = self.input_box.text()
        self.char_counter.update_count(text)
        self.update_send_button_state()
        
        # Update input box style based on character count
        if len(text) > self.MAX_CHARS:
            self.input_box.setProperty("invalid", True)
        else:
            self.input_box.setProperty("invalid", False)
        self.input_box.style().polish(self.input_box)
        
    def update_send_button_state(self):
        """Enable/disable send button based on character count"""
        text = self.input_box.text().strip()
        char_count = len(text)
        
        # Disable if text is empty or exceeds max characters
        if not text or char_count > self.MAX_CHARS:
            self.send_button.setEnabled(False)
        else:
            self.send_button.setEnabled(True)
            
    def play_sound(self, sound_type):
        """Play sound effects for interactions"""
        if not SOUND_ENABLED:
            return
            
        try:
            if sound_type == "send":
                # Generate a beep sound
                pygame.mixer.Sound(buffer=bytes([128 + int(127 * (i % 255) / 255) 
                    for i in range(44100 // 4)])).play()
            elif sound_type == "button":
                pygame.mixer.Sound(buffer=bytes([128 + int(127 * (i % 128) / 127) 
                    for i in range(44100 // 8)])).play()
            elif sound_type == "receive":
                pygame.mixer.Sound(buffer=bytes([128 + int(127 * (i % 512) / 511) 
                    for i in range(44100 // 2)])).play()
            elif sound_type == "error":
                pygame.mixer.Sound(buffer=bytes([128 + int(127 * (i % 64) / 63) 
                    for i in range(44100 // 16)])).play()
        except:
            pass

    def send_sync_cmd(self):
        """Send synchronization command"""
        self.play_sound("button")
        sync_cmd_message = "T"
        try:
            self.message_port_pub(pmt.intern("sync_cmd"), pmt.intern(sync_cmd_message))
        except Exception:
            self.message_port_pub(pmt.intern("sync_cmd"), pmt.intern(sync_cmd_message))
        
        # Show sync animation
        self.sync_button.setText("🔄 SYNCING...")
        QtCore.QTimer.singleShot(1000, lambda: self.sync_button.setText("🔄 SYNC"))

    def send_message(self):
        """Called from GUI thread when user sends a message."""
        text = self.input_box.text().strip()
        if not text:
            return
            
        # Check character limit
        if len(text) > self.MAX_CHARS:
            self.play_sound("error")
            # Show error animation
            self.input_box.setStyleSheet("""
                QLineEdit {
                    background-color: #FFF5F5;
                    border: 2px solid #E53E3E;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 14px;
                }
            """)
            QtCore.QTimer.singleShot(500, lambda: self.input_box.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 2px solid #CBD5E0;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border-color: #4299E1;
                }
            """))
            return

        self.play_sound("send")
        
        # Get the numeric address from the selected item's userData
        selected_index = self.addr_box.currentIndex()
        numeric_address = self.addr_box.itemData(selected_index)
        
        if not numeric_address:
            # Fallback: extract number from display text
            display_text = self.addr_box.currentText()
            # Try to extract number from "Station X" format
            import re
            match = re.search(r'(\d+)', display_text)
            if match:
                numeric_address = match.group(1)
            else:
                # Default to station 1
                numeric_address = "1"
        
        # Create the message in "addr:body" format with numeric address
        full_msg = f"{numeric_address}:{text}"
        
        # Get display text for GUI
        display_address = self.addr_box.currentText()

        # Publish as PMT symbol/string on 'out' port
        try:
            self.message_port_pub(pmt.intern("out"), pmt.intern(full_msg))
        except Exception:
            self.message_port_pub(pmt.intern("out"), pmt.intern(full_msg))

        # Create and display message bubble
        message_widget = MessageBubble(
            text, 
            is_outgoing=True, 
            address=display_address,
            numeric_address=numeric_address
        )
        self.chat_layout.addWidget(message_widget, alignment=QtCore.Qt.AlignRight)
        
        # Store widget reference for feedback
        self.message_counter += 1
        msg_id = f"msg_{self.message_counter}"
        self.message_widgets[msg_id] = message_widget

        # Clear input and scroll to bottom
        self.input_box.clear()
        QtCore.QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def _process_feedback(self, msg_pmt):
        """
        Handler for 'feedback' port. Expected feedback values:
          - "TRUE" => message delivered
          - "FALSE" => delivery failed
        """
        try:
            if pmt.is_symbol(msg_pmt) or pmt.is_string(msg_pmt):
                fb = pmt.symbol_to_string(msg_pmt)
            else:
                py = pmt.to_python(msg_pmt)
                fb = str(py)
        except Exception:
            fb = "<unreadable feedback>"

        # Update the most recent outgoing message's status
        if self.message_widgets:
            # Get the most recent message
            msg_id = f"msg_{self.message_counter}"
            if msg_id in self.message_widgets:
                msg_widget = self.message_widgets[msg_id]
                if fb == "TRUE":
                    msg_widget.status_label.setText("✅ Delivered")
                    msg_widget.status_label.setStyleSheet("""
                        QLabel {
                            color: #38A169;
                            font-size: 10px;
                            font-weight: bold;
                        }
                    """)
                elif fb == "FALSE":
                    msg_widget.status_label.setText("❌ Failed")
                    msg_widget.status_label.setStyleSheet("""
                        QLabel {
                            color: #E53E3E;
                            font-size: 10px;
                            font-weight: bold;
                        }
                    """)

    def _receive_message(self, msg_pmt):
        """
        Handler for 'in_msg' port. Extracts string and posts it to GUI thread.
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
            try:
                self._display_incoming(s)
            except Exception:
                print("[Hospital Paging] failed to deliver incoming message to GUI:", s)

    def _display_incoming(self, full_msg):
        """
        Display incoming message bubble.
        full_msg expected in "addr:body" format with numeric address.
        """
        self.play_sound("receive")
        
        # Parse numeric address and body
        if ":" in full_msg:
            numeric_address, body = full_msg.split(":", 1)
            
            # Convert numeric address to display name
            try:
                addr_num = int(numeric_address)
                if 1 <= addr_num <= 10:
                    display_address = f"Station {addr_num}"
                elif addr_num == 11:
                    display_address = "Emergency Room"
                elif addr_num == 12:
                    display_address = "Pharmacy"
                elif addr_num == 13:
                    display_address = "Lab"
                elif addr_num == 14:
                    display_address = "Radiology"
                else:
                    display_address = f"Station {addr_num}"
            except ValueError:
                display_address = f"Station {numeric_address}"
        else:
            display_address = "Unknown Station"
            numeric_address = "?"
            body = full_msg

        # Create and display message bubble
        message_widget = MessageBubble(
            body, 
            is_outgoing=False, 
            address=display_address,
            numeric_address=numeric_address
        )
        self.chat_layout.addWidget(message_widget, alignment=QtCore.Qt.AlignLeft)

        # Scroll to bottom
        QtCore.QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))