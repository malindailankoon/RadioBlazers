#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: cdp
# Author: BellLabz
# Description: cdp project
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import blocks
from gnuradio import channels
from gnuradio.filter import firdes
from gnuradio import digital
from gnuradio import filter
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import gr, pdu
import cdp_epy_block_0 as epy_block_0  # embedded python block
import cdp_epy_block_0_1_0 as epy_block_0_1_0  # embedded python block
import cdp_epy_block_2_0 as epy_block_2_0  # embedded python block
import cdp_epy_block_3 as epy_block_3  # embedded python block
import cdp_epy_block_3_0 as epy_block_3_0  # embedded python block
import cdp_epy_block_3_1 as epy_block_3_1  # embedded python block
import cdp_epy_block_4_0 as epy_block_4_0  # embedded python block
import sip
import threading



class cdp(gr.top_block, Qt.QWidget):

    def __init__(self, MTU=1500):
        gr.top_block.__init__(self, "cdp", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("cdp")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "cdp")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Parameters
        ##################################################
        self.MTU = MTU

        ##################################################
        # Variables
        ##################################################
        self.sps = sps = 4
        self.qpsk = qpsk = digital.constellation_rect([0.707+0.707j, -0.707+0.707j, -0.707-0.707j, 0.707-0.707j], [0, 1, 2, 3],
        4, 2, 2, 1, 1).base()
        self.nfilts = nfilts = 32
        self.variable_qtgui_entry_0 = variable_qtgui_entry_0 = ''
        self.variable_adaptive_algorithm_0 = variable_adaptive_algorithm_0 = digital.adaptive_algorithm_cma( qpsk, .0001, 4).base()
        self.txbw = txbw = 9000
        self.timing_loop_bw = timing_loop_bw = 6.28/100.0
        self.time_offset = time_offset = 1.00
        self.spr = spr = 750000
        self.samp_rate_blade = samp_rate_blade = 600e3
        self.samp_rate = samp_rate = 600e3
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(nfilts, nfilts, 1.0/float(sps), 0.35, 11*sps*nfilts)
        self.rf_gain_0 = rf_gain_0 = 60
        self.polys = polys = [109, 79]
        self.phase_bw = phase_bw = 6.28/100.0
        self.noise_volt = noise_volt = 0.4
        self.k = k = 7
        self.hdr_format = hdr_format = digital.header_format_default('11100001010110101110100010010011',1, 1)
        self.freq_offset = freq_offset = 0
        self.excess_bw = excess_bw = .5
        self.eq_gain = eq_gain = 0.01
        self.arity = arity = 4

        ##################################################
        # Blocks
        ##################################################

        self.controls = Qt.QTabWidget()
        self.controls_widget_0 = Qt.QWidget()
        self.controls_layout_0 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.controls_widget_0)
        self.controls_grid_layout_0 = Qt.QGridLayout()
        self.controls_layout_0.addLayout(self.controls_grid_layout_0)
        self.controls.addTab(self.controls_widget_0, 'Channel')
        self.controls_widget_1 = Qt.QWidget()
        self.controls_layout_1 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.controls_widget_1)
        self.controls_grid_layout_1 = Qt.QGridLayout()
        self.controls_layout_1.addLayout(self.controls_grid_layout_1)
        self.controls.addTab(self.controls_widget_1, 'Receiver')
        self.top_grid_layout.addWidget(self.controls, 0, 0, 1, 2)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._time_offset_range = qtgui.Range(0.999, 1.001, 0.0001, 1.00, 200)
        self._time_offset_win = qtgui.RangeWidget(self._time_offset_range, self.set_time_offset, "Timing Offset", "counter_slider", float, QtCore.Qt.Horizontal)
        self.controls_grid_layout_0.addWidget(self._time_offset_win, 0, 2, 1, 1)
        for r in range(0, 1):
            self.controls_grid_layout_0.setRowStretch(r, 1)
        for c in range(2, 3):
            self.controls_grid_layout_0.setColumnStretch(c, 1)
        self.received = Qt.QTabWidget()
        self.received_widget_0 = Qt.QWidget()
        self.received_layout_0 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.received_widget_0)
        self.received_grid_layout_0 = Qt.QGridLayout()
        self.received_layout_0.addLayout(self.received_grid_layout_0)
        self.received.addTab(self.received_widget_0, 'Constellation')
        self.received_widget_1 = Qt.QWidget()
        self.received_layout_1 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.received_widget_1)
        self.received_grid_layout_1 = Qt.QGridLayout()
        self.received_layout_1.addLayout(self.received_grid_layout_1)
        self.received.addTab(self.received_widget_1, 'Symbols')
        self.top_grid_layout.addWidget(self.received, 2, 0, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._phase_bw_range = qtgui.Range(0.0, 1.0, 0.01, 6.28/100.0, 200)
        self._phase_bw_win = qtgui.RangeWidget(self._phase_bw_range, self.set_phase_bw, "Phase: Bandwidth", "slider", float, QtCore.Qt.Horizontal)
        self.controls_grid_layout_1.addWidget(self._phase_bw_win, 0, 2, 1, 1)
        for r in range(0, 1):
            self.controls_grid_layout_1.setRowStretch(r, 1)
        for c in range(2, 3):
            self.controls_grid_layout_1.setColumnStretch(c, 1)
        self._noise_volt_range = qtgui.Range(0, 1, 0.01, 0.4, 200)
        self._noise_volt_win = qtgui.RangeWidget(self._noise_volt_range, self.set_noise_volt, "Noise Voltage", "counter_slider", float, QtCore.Qt.Horizontal)
        self.controls_grid_layout_0.addWidget(self._noise_volt_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.controls_grid_layout_0.setRowStretch(r, 1)
        for c in range(0, 1):
            self.controls_grid_layout_0.setColumnStretch(c, 1)
        self._freq_offset_range = qtgui.Range(-0.1, 0.1, 0.001, 0, 200)
        self._freq_offset_win = qtgui.RangeWidget(self._freq_offset_range, self.set_freq_offset, "Frequency Offset", "counter_slider", float, QtCore.Qt.Horizontal)
        self.controls_grid_layout_0.addWidget(self._freq_offset_win, 0, 1, 1, 1)
        for r in range(0, 1):
            self.controls_grid_layout_0.setRowStretch(r, 1)
        for c in range(1, 2):
            self.controls_grid_layout_0.setColumnStretch(c, 1)
        self._variable_qtgui_entry_0_tool_bar = Qt.QToolBar(self)
        self._variable_qtgui_entry_0_tool_bar.addWidget(Qt.QLabel("'variable_qtgui_entry_0'" + ": "))
        self._variable_qtgui_entry_0_line_edit = Qt.QLineEdit(str(self.variable_qtgui_entry_0))
        self._variable_qtgui_entry_0_tool_bar.addWidget(self._variable_qtgui_entry_0_line_edit)
        self._variable_qtgui_entry_0_line_edit.editingFinished.connect(
            lambda: self.set_variable_qtgui_entry_0(str(str(self._variable_qtgui_entry_0_line_edit.text()))))
        self.top_layout.addWidget(self._variable_qtgui_entry_0_tool_bar)
        self._timing_loop_bw_range = qtgui.Range(0.0, 0.2, 0.01, 6.28/100.0, 200)
        self._timing_loop_bw_win = qtgui.RangeWidget(self._timing_loop_bw_range, self.set_timing_loop_bw, "Time: BW", "slider", float, QtCore.Qt.Horizontal)
        self.controls_grid_layout_1.addWidget(self._timing_loop_bw_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.controls_grid_layout_1.setRowStretch(r, 1)
        for c in range(0, 1):
            self.controls_grid_layout_1.setColumnStretch(c, 1)
        self._rf_gain_0_range = qtgui.Range(0, 60, 1, 60, 200)
        self._rf_gain_0_win = qtgui.RangeWidget(self._rf_gain_0_range, self.set_rf_gain_0, "RF gain", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rf_gain_0_win)
        self.qtgui_time_sink_x_0 = qtgui.time_sink_f(
            500, #size
            samp_rate, #samp_rate
            '', #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0.set_y_axis(-1, 4)

        self.qtgui_time_sink_x_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0.enable_tags(True)
        self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0.enable_autoscale(False)
        self.qtgui_time_sink_x_0.enable_grid(False)
        self.qtgui_time_sink_x_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0.enable_stem_plot(False)


        labels = ['Symbols', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.qwidget(), Qt.QWidget)
        self.received_grid_layout_1.addWidget(self._qtgui_time_sink_x_0_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.received_grid_layout_1.setRowStretch(r, 1)
        for c in range(0, 1):
            self.received_grid_layout_1.setColumnStretch(c, 1)
        self.qtgui_freq_sink_x_1_0 = qtgui.freq_sink_c(
            256, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            'RX-SPECTRUM of ACK', #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_1_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_1_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_1_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_1_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_1_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_1_0.enable_grid(False)
        self.qtgui_freq_sink_x_1_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_1_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_1_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_1_0.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_1_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_1_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_1_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_1_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_1_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_1_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_1_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_freq_sink_x_1_0_win)
        self.qtgui_freq_sink_x_1 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            'RX-SPECTRUM', #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_1.set_update_time(0.10)
        self.qtgui_freq_sink_x_1.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_1.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_1.enable_autoscale(False)
        self.qtgui_freq_sink_x_1.enable_grid(False)
        self.qtgui_freq_sink_x_1.set_fft_average(1.0)
        self.qtgui_freq_sink_x_1.enable_axis_labels(True)
        self.qtgui_freq_sink_x_1.enable_control_panel(False)
        self.qtgui_freq_sink_x_1.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_1.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_1.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_1.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_1.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_1_win = sip.wrapinstance(self.qtgui_freq_sink_x_1.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_freq_sink_x_1_win)
        self.qtgui_freq_sink_x_0_0 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            'TX - Spectrum of ACK', #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_0_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0_0.enable_grid(False)
        self.qtgui_freq_sink_x_0_0.set_fft_average(0.05)
        self.qtgui_freq_sink_x_0_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0_0.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_freq_sink_x_0_0_win)
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            'TX - Spectrum', #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0.enable_grid(False)
        self.qtgui_freq_sink_x_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_freq_sink_x_0_win)
        self.qtgui_const_sink_x_0_0 = qtgui.const_sink_c(
            1024, #size
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_0_0.set_update_time(0.10)
        self.qtgui_const_sink_x_0_0.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_0_0.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_0_0.enable_autoscale(False)
        self.qtgui_const_sink_x_0_0.enable_grid(False)
        self.qtgui_const_sink_x_0_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
            "red", "red", "red", "red", "red"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_0_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_0_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_0_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_0_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_0_0_win = sip.wrapinstance(self.qtgui_const_sink_x_0_0.qwidget(), Qt.QWidget)
        self.received_grid_layout_0.addWidget(self._qtgui_const_sink_x_0_0_win, 0, 1, 1, 1)
        for r in range(0, 1):
            self.received_grid_layout_0.setRowStretch(r, 1)
        for c in range(1, 2):
            self.received_grid_layout_0.setColumnStretch(c, 1)
        self.qtgui_const_sink_x_0 = qtgui.const_sink_c(
            1024, #size
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_0.set_update_time(0.10)
        self.qtgui_const_sink_x_0.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_0.enable_autoscale(False)
        self.qtgui_const_sink_x_0.enable_grid(False)
        self.qtgui_const_sink_x_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
            "red", "red", "red", "red", "red"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_0_win = sip.wrapinstance(self.qtgui_const_sink_x_0.qwidget(), Qt.QWidget)
        self.received_grid_layout_0.addWidget(self._qtgui_const_sink_x_0_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.received_grid_layout_0.setRowStretch(r, 1)
        for c in range(0, 1):
            self.received_grid_layout_0.setColumnStretch(c, 1)
        self.pdu_tagged_stream_to_pdu_0_0 = pdu.tagged_stream_to_pdu(gr.types.byte_t, 'packet_len')
        self.pdu_tagged_stream_to_pdu_0 = pdu.tagged_stream_to_pdu(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0_1 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0_0_0 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0_0 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self._eq_gain_range = qtgui.Range(0.0, 0.1, 0.001, 0.01, 200)
        self._eq_gain_win = qtgui.RangeWidget(self._eq_gain_range, self.set_eq_gain, "Equalizer: rate", "slider", float, QtCore.Qt.Horizontal)
        self.controls_grid_layout_1.addWidget(self._eq_gain_win, 0, 1, 1, 1)
        for r in range(0, 1):
            self.controls_grid_layout_1.setRowStretch(r, 1)
        for c in range(1, 2):
            self.controls_grid_layout_1.setColumnStretch(c, 1)
        self.epy_block_4_0 = epy_block_4_0.crc_forwarder()
        self.epy_block_3_1 = epy_block_3_1.multi_sender_gui(bg_image='/home/vboxuser/Downloads/Networks_Telecommunications.jpg')
        self.epy_block_3_0 = epy_block_3_0.address_check(my_address=21)
        self.epy_block_3 = epy_block_3.address_check(my_address=20)
        self.epy_block_2_0 = epy_block_2_0.pdu_text_gui(wait_time=0.2, pkt_size=32, address=21, retry_limit=16, window_size=7)
        self.epy_block_0_1_0 = epy_block_0_1_0.messenger_gui(bg_image='/home/vboxuser/Downloads/tx.jpg')
        self.epy_block_0 = epy_block_0.address_add(address=20)
        self.digital_symbol_sync_xx_0_0 = digital.symbol_sync_cc(
            digital.TED_SIGNAL_TIMES_SLOPE_ML,
            sps,
            phase_bw,
            1.0,
            1.0,
            1.5,
            4,
            digital.constellation_bpsk().base(),
            digital.IR_PFB_MF,
            32,
            rrc_taps)
        self.digital_symbol_sync_xx_0 = digital.symbol_sync_cc(
            digital.TED_SIGNAL_TIMES_SLOPE_ML,
            sps,
            phase_bw,
            1.0,
            1.0,
            1.5,
            4,
            digital.constellation_bpsk().base(),
            digital.IR_PFB_MF,
            32,
            rrc_taps)
        self.digital_protocol_formatter_async_0_0 = digital.protocol_formatter_async(hdr_format)
        self.digital_protocol_formatter_async_0 = digital.protocol_formatter_async(hdr_format)
        self.digital_map_bb_0_0 = digital.map_bb([0,1,2,3])
        self.digital_map_bb_0 = digital.map_bb([0,1,2,3])
        self.digital_linear_equalizer_0_0_0 = digital.linear_equalizer(15, 4, variable_adaptive_algorithm_0, True, [ ], 'corr_est')
        self.digital_linear_equalizer_0_0 = digital.linear_equalizer(32, 4, variable_adaptive_algorithm_0, True, [ ], 'corr_est')
        self.digital_diff_decoder_bb_0_0 = digital.diff_decoder_bb(4, digital.DIFF_DIFFERENTIAL)
        self.digital_diff_decoder_bb_0 = digital.diff_decoder_bb(4, digital.DIFF_DIFFERENTIAL)
        self.digital_crc_append_0 = digital.crc_append(32, 0x4C11DB7, 0xFFFFFFFF, 0xFFFFFFFF, True, True, False, 0)
        self.digital_costas_loop_cc_0_0 = digital.costas_loop_cc(phase_bw, arity, False)
        self.digital_costas_loop_cc_0 = digital.costas_loop_cc(phase_bw, arity, False)
        self.digital_correlate_access_code_xx_ts_0_0 = digital.correlate_access_code_bb_ts('11100001010110101110100010010011',
          1, "packet_len")
        self.digital_correlate_access_code_xx_ts_0 = digital.correlate_access_code_bb_ts('11100001010110101110100010010011',
          2, "packet_len")
        self.digital_constellation_modulator_0_0 = digital.generic_mod(
            constellation=qpsk,
            differential=True,
            samples_per_symbol=sps,
            pre_diff_code=True,
            excess_bw=excess_bw,
            verbose=False,
            log=False,
            truncate=False)
        self.digital_constellation_modulator_0 = digital.generic_mod(
            constellation=qpsk,
            differential=True,
            samples_per_symbol=sps,
            pre_diff_code=True,
            excess_bw=excess_bw,
            verbose=False,
            log=False,
            truncate=False)
        self.digital_constellation_decoder_cb_0_0 = digital.constellation_decoder_cb(qpsk)
        self.digital_constellation_decoder_cb_0 = digital.constellation_decoder_cb(qpsk)
        self.channels_channel_model_0_0 = channels.channel_model(
            noise_voltage=noise_volt,
            frequency_offset=freq_offset,
            epsilon=time_offset,
            taps=[3],
            noise_seed=0,
            block_tags=False)
        self.channels_channel_model_0 = channels.channel_model(
            noise_voltage=noise_volt,
            frequency_offset=freq_offset,
            epsilon=time_offset,
            taps=[3],
            noise_seed=0,
            block_tags=False)
        self.blocks_unpack_k_bits_bb_0_0 = blocks.unpack_k_bits_bb(2)
        self.blocks_unpack_k_bits_bb_0 = blocks.unpack_k_bits_bb(2)
        self.blocks_throttle2_0_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_tagged_stream_mux_0_0 = blocks.tagged_stream_mux(gr.sizeof_char*1, "packet_len", 0)
        self.blocks_tagged_stream_mux_0 = blocks.tagged_stream_mux(gr.sizeof_char*1, "packet_len", 0)
        self.blocks_repack_bits_bb_1_0 = blocks.repack_bits_bb(1, 8, "packet_len", False, gr.GR_MSB_FIRST)
        self.blocks_repack_bits_bb_1 = blocks.repack_bits_bb(1, 8, "packet_len", False, gr.GR_MSB_FIRST)
        self.blocks_char_to_float_0 = blocks.char_to_float(1, 1)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.digital_crc_append_0, 'out'), (self.epy_block_0, 'in'))
        self.msg_connect((self.digital_protocol_formatter_async_0, 'header'), (self.pdu_pdu_to_tagged_stream_0, 'pdus'))
        self.msg_connect((self.digital_protocol_formatter_async_0, 'payload'), (self.pdu_pdu_to_tagged_stream_0_0, 'pdus'))
        self.msg_connect((self.digital_protocol_formatter_async_0_0, 'payload'), (self.pdu_pdu_to_tagged_stream_0_0_0, 'pdus'))
        self.msg_connect((self.digital_protocol_formatter_async_0_0, 'header'), (self.pdu_pdu_to_tagged_stream_0_1, 'pdus'))
        self.msg_connect((self.epy_block_0, 'out'), (self.digital_protocol_formatter_async_0, 'in'))
        self.msg_connect((self.epy_block_0_1_0, 'out'), (self.epy_block_2_0, 'in'))
        self.msg_connect((self.epy_block_2_0, 'out'), (self.digital_crc_append_0, 'in'))
        self.msg_connect((self.epy_block_2_0, 'feedback'), (self.epy_block_0_1_0, 'feedback'))
        self.msg_connect((self.epy_block_3, 'out'), (self.epy_block_4_0, 'in'))
        self.msg_connect((self.epy_block_3_0, 'out'), (self.epy_block_2_0, 'ack_in'))
        self.msg_connect((self.epy_block_4_0, 'ack_out'), (self.digital_protocol_formatter_async_0_0, 'in'))
        self.msg_connect((self.epy_block_4_0, 'out'), (self.epy_block_3_1, 'in'))
        self.msg_connect((self.pdu_tagged_stream_to_pdu_0, 'pdus'), (self.epy_block_3, 'in'))
        self.msg_connect((self.pdu_tagged_stream_to_pdu_0_0, 'pdus'), (self.epy_block_3_0, 'in'))
        self.connect((self.blocks_char_to_float_0, 0), (self.qtgui_time_sink_x_0, 0))
        self.connect((self.blocks_repack_bits_bb_1, 0), (self.pdu_tagged_stream_to_pdu_0, 0))
        self.connect((self.blocks_repack_bits_bb_1_0, 0), (self.pdu_tagged_stream_to_pdu_0_0, 0))
        self.connect((self.blocks_tagged_stream_mux_0, 0), (self.digital_constellation_modulator_0, 0))
        self.connect((self.blocks_tagged_stream_mux_0_0, 0), (self.digital_constellation_modulator_0_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.channels_channel_model_0, 0))
        self.connect((self.blocks_throttle2_0_0, 0), (self.channels_channel_model_0_0, 0))
        self.connect((self.blocks_unpack_k_bits_bb_0, 0), (self.digital_correlate_access_code_xx_ts_0, 0))
        self.connect((self.blocks_unpack_k_bits_bb_0_0, 0), (self.digital_correlate_access_code_xx_ts_0_0, 0))
        self.connect((self.channels_channel_model_0, 0), (self.digital_symbol_sync_xx_0, 0))
        self.connect((self.channels_channel_model_0, 0), (self.qtgui_freq_sink_x_1, 0))
        self.connect((self.channels_channel_model_0_0, 0), (self.digital_symbol_sync_xx_0_0, 0))
        self.connect((self.channels_channel_model_0_0, 0), (self.qtgui_freq_sink_x_1_0, 0))
        self.connect((self.digital_constellation_decoder_cb_0, 0), (self.blocks_char_to_float_0, 0))
        self.connect((self.digital_constellation_decoder_cb_0, 0), (self.digital_diff_decoder_bb_0, 0))
        self.connect((self.digital_constellation_decoder_cb_0_0, 0), (self.digital_diff_decoder_bb_0_0, 0))
        self.connect((self.digital_constellation_modulator_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.digital_constellation_modulator_0, 0), (self.qtgui_freq_sink_x_0, 0))
        self.connect((self.digital_constellation_modulator_0_0, 0), (self.blocks_throttle2_0_0, 0))
        self.connect((self.digital_constellation_modulator_0_0, 0), (self.qtgui_freq_sink_x_0_0, 0))
        self.connect((self.digital_correlate_access_code_xx_ts_0, 0), (self.blocks_repack_bits_bb_1, 0))
        self.connect((self.digital_correlate_access_code_xx_ts_0_0, 0), (self.blocks_repack_bits_bb_1_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.digital_constellation_decoder_cb_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.qtgui_const_sink_x_0, 0))
        self.connect((self.digital_costas_loop_cc_0_0, 0), (self.digital_constellation_decoder_cb_0_0, 0))
        self.connect((self.digital_costas_loop_cc_0_0, 0), (self.qtgui_const_sink_x_0_0, 0))
        self.connect((self.digital_diff_decoder_bb_0, 0), (self.digital_map_bb_0, 0))
        self.connect((self.digital_diff_decoder_bb_0_0, 0), (self.digital_map_bb_0_0, 0))
        self.connect((self.digital_linear_equalizer_0_0, 0), (self.digital_costas_loop_cc_0, 0))
        self.connect((self.digital_linear_equalizer_0_0_0, 0), (self.digital_costas_loop_cc_0_0, 0))
        self.connect((self.digital_map_bb_0, 0), (self.blocks_unpack_k_bits_bb_0, 0))
        self.connect((self.digital_map_bb_0_0, 0), (self.blocks_unpack_k_bits_bb_0_0, 0))
        self.connect((self.digital_symbol_sync_xx_0, 0), (self.digital_linear_equalizer_0_0, 0))
        self.connect((self.digital_symbol_sync_xx_0_0, 0), (self.digital_linear_equalizer_0_0_0, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0, 0), (self.blocks_tagged_stream_mux_0, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0_0, 0), (self.blocks_tagged_stream_mux_0, 1))
        self.connect((self.pdu_pdu_to_tagged_stream_0_0_0, 0), (self.blocks_tagged_stream_mux_0_0, 1))
        self.connect((self.pdu_pdu_to_tagged_stream_0_1, 0), (self.blocks_tagged_stream_mux_0_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "cdp")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_MTU(self):
        return self.MTU

    def set_MTU(self, MTU):
        self.MTU = MTU

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts, 1.0/float(self.sps), 0.35, 11*self.sps*self.nfilts))
        self.digital_symbol_sync_xx_0.set_sps(self.sps)
        self.digital_symbol_sync_xx_0_0.set_sps(self.sps)

    def get_qpsk(self):
        return self.qpsk

    def set_qpsk(self, qpsk):
        self.qpsk = qpsk
        self.digital_constellation_decoder_cb_0.set_constellation(self.qpsk)
        self.digital_constellation_decoder_cb_0_0.set_constellation(self.qpsk)

    def get_nfilts(self):
        return self.nfilts

    def set_nfilts(self, nfilts):
        self.nfilts = nfilts
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts, 1.0/float(self.sps), 0.35, 11*self.sps*self.nfilts))

    def get_variable_qtgui_entry_0(self):
        return self.variable_qtgui_entry_0

    def set_variable_qtgui_entry_0(self, variable_qtgui_entry_0):
        self.variable_qtgui_entry_0 = variable_qtgui_entry_0
        Qt.QMetaObject.invokeMethod(self._variable_qtgui_entry_0_line_edit, "setText", Qt.Q_ARG("QString", str(self.variable_qtgui_entry_0)))

    def get_variable_adaptive_algorithm_0(self):
        return self.variable_adaptive_algorithm_0

    def set_variable_adaptive_algorithm_0(self, variable_adaptive_algorithm_0):
        self.variable_adaptive_algorithm_0 = variable_adaptive_algorithm_0

    def get_txbw(self):
        return self.txbw

    def set_txbw(self, txbw):
        self.txbw = txbw

    def get_timing_loop_bw(self):
        return self.timing_loop_bw

    def set_timing_loop_bw(self, timing_loop_bw):
        self.timing_loop_bw = timing_loop_bw

    def get_time_offset(self):
        return self.time_offset

    def set_time_offset(self, time_offset):
        self.time_offset = time_offset
        self.channels_channel_model_0.set_timing_offset(self.time_offset)
        self.channels_channel_model_0_0.set_timing_offset(self.time_offset)

    def get_spr(self):
        return self.spr

    def set_spr(self, spr):
        self.spr = spr

    def get_samp_rate_blade(self):
        return self.samp_rate_blade

    def set_samp_rate_blade(self, samp_rate_blade):
        self.samp_rate_blade = samp_rate_blade

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)
        self.blocks_throttle2_0_0.set_sample_rate(self.samp_rate)
        self.qtgui_freq_sink_x_0.set_frequency_range(0, self.samp_rate)
        self.qtgui_freq_sink_x_0_0.set_frequency_range(0, self.samp_rate)
        self.qtgui_freq_sink_x_1.set_frequency_range(0, self.samp_rate)
        self.qtgui_freq_sink_x_1_0.set_frequency_range(0, self.samp_rate)
        self.qtgui_time_sink_x_0.set_samp_rate(self.samp_rate)

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps

    def get_rf_gain_0(self):
        return self.rf_gain_0

    def set_rf_gain_0(self, rf_gain_0):
        self.rf_gain_0 = rf_gain_0

    def get_polys(self):
        return self.polys

    def set_polys(self, polys):
        self.polys = polys

    def get_phase_bw(self):
        return self.phase_bw

    def set_phase_bw(self, phase_bw):
        self.phase_bw = phase_bw
        self.digital_costas_loop_cc_0.set_loop_bandwidth(self.phase_bw)
        self.digital_costas_loop_cc_0_0.set_loop_bandwidth(self.phase_bw)
        self.digital_symbol_sync_xx_0.set_loop_bandwidth(self.phase_bw)
        self.digital_symbol_sync_xx_0_0.set_loop_bandwidth(self.phase_bw)

    def get_noise_volt(self):
        return self.noise_volt

    def set_noise_volt(self, noise_volt):
        self.noise_volt = noise_volt
        self.channels_channel_model_0.set_noise_voltage(self.noise_volt)
        self.channels_channel_model_0_0.set_noise_voltage(self.noise_volt)

    def get_k(self):
        return self.k

    def set_k(self, k):
        self.k = k

    def get_hdr_format(self):
        return self.hdr_format

    def set_hdr_format(self, hdr_format):
        self.hdr_format = hdr_format

    def get_freq_offset(self):
        return self.freq_offset

    def set_freq_offset(self, freq_offset):
        self.freq_offset = freq_offset
        self.channels_channel_model_0.set_frequency_offset(self.freq_offset)
        self.channels_channel_model_0_0.set_frequency_offset(self.freq_offset)

    def get_excess_bw(self):
        return self.excess_bw

    def set_excess_bw(self, excess_bw):
        self.excess_bw = excess_bw

    def get_eq_gain(self):
        return self.eq_gain

    def set_eq_gain(self, eq_gain):
        self.eq_gain = eq_gain

    def get_arity(self):
        return self.arity

    def set_arity(self, arity):
        self.arity = arity



def argument_parser():
    description = 'cdp project'
    parser = ArgumentParser(description=description)
    parser.add_argument(
        "--MTU", dest="MTU", type=intx, default=1500,
        help="Set MTU [default=%(default)r]")
    return parser


def main(top_block_cls=cdp, options=None):
    if options is None:
        options = argument_parser().parse_args()

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(MTU=options.MTU)

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
