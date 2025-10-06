#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
import pmt
from gnuradio import blocks, gr
from gnuradio import digital
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import threading
import threading1_epy_block_0 as epy_block_0  # embedded python block
import threading1_epy_block_0_0 as epy_block_0_0  # embedded python block
import threading1_epy_block_1 as epy_block_1  # embedded python block
import threading1_epy_block_1_0 as epy_block_1_0  # embedded python block
import threading1_epy_block_2 as epy_block_2  # embedded python block
import threading1_epy_block_2_0 as epy_block_2_0  # embedded python block



class threading1(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Not titled yet")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "threading1")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.sps = sps = 4
        self.qpsk = qpsk = digital.constellation_rect([0.707+0.707j, -0.707+0.707j, -0.707-0.707j, 0.707-0.707j], [0, 1, 2, 3],
        4, 2, 2, 1, 1).base()
        self.nfilts = nfilts = 32
        self.variable_adaptive_algorithm_0 = variable_adaptive_algorithm_0 = digital.adaptive_algorithm_cma( qpsk, .0001, 4).base()
        self.taps = taps = [1.0, 0.25-0.25j, 0.50 + 0.10j, -0.3 + 0.2j]
        self.samp_rate = samp_rate = 32000
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(nfilts, nfilts, 1.0/float(sps), 0.35, 11*sps*nfilts)
        self.access_key = access_key = '101010101010101010101010101010100010110111010100'

        ##################################################
        # Blocks
        ##################################################

        self.epy_block_2_0 = epy_block_2_0.bitstream_to_pdu(sync_word=0x1ACFFC1D, threshold=1)
        self.epy_block_2 = epy_block_2.bitstream_to_pdu(sync_word=0x1ACFFC1D, threshold=1)
        self.epy_block_1_0 = epy_block_1_0.pdu_to_bitstream(sync_word=0x1ACFFC1D)
        self.epy_block_1 = epy_block_1.pdu_to_bitstream(sync_word=0x1ACFFC1D)
        self.epy_block_0_0 = epy_block_0_0.blk(node_id=2, aloha_prob=0.5, timeout=1, max_retries=3)
        self.epy_block_0 = epy_block_0.blk(node_id=1, aloha_prob=0.5, timeout=1, max_retries=3)
        self.blocks_message_strobe_0_0 = blocks.message_strobe(pmt.intern("1:Hello from B"), 1000)
        self.blocks_message_strobe_0 = blocks.message_strobe(pmt.intern("2:Hello from A"), 1000)
        self.blocks_message_debug_0_0 = blocks.message_debug(True, gr.log_levels.info)
        self.blocks_message_debug_0 = blocks.message_debug(True, gr.log_levels.info)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_message_strobe_0, 'strobe'), (self.epy_block_0, 'msg_in'))
        self.msg_connect((self.blocks_message_strobe_0_0, 'strobe'), (self.epy_block_0_0, 'msg_in'))
        self.msg_connect((self.epy_block_0, 'msg_out'), (self.blocks_message_debug_0_0, 'print'))
        self.msg_connect((self.epy_block_0, 'pdu_out'), (self.epy_block_1, 'pdu_in'))
        self.msg_connect((self.epy_block_0_0, 'msg_out'), (self.blocks_message_debug_0, 'print'))
        self.msg_connect((self.epy_block_0_0, 'pdu_out'), (self.epy_block_1_0, 'pdu_in'))
        self.msg_connect((self.epy_block_2, 'pdu_out'), (self.epy_block_0_0, 'pdu_in'))
        self.msg_connect((self.epy_block_2_0, 'pdu_out'), (self.epy_block_0, 'pdu_in'))
        self.connect((self.epy_block_1, 0), (self.epy_block_2, 0))
        self.connect((self.epy_block_1_0, 0), (self.epy_block_2_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "threading1")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts, 1.0/float(self.sps), 0.35, 11*self.sps*self.nfilts))

    def get_qpsk(self):
        return self.qpsk

    def set_qpsk(self, qpsk):
        self.qpsk = qpsk

    def get_nfilts(self):
        return self.nfilts

    def set_nfilts(self, nfilts):
        self.nfilts = nfilts
        self.set_rrc_taps(firdes.root_raised_cosine(self.nfilts, self.nfilts, 1.0/float(self.sps), 0.35, 11*self.sps*self.nfilts))

    def get_variable_adaptive_algorithm_0(self):
        return self.variable_adaptive_algorithm_0

    def set_variable_adaptive_algorithm_0(self, variable_adaptive_algorithm_0):
        self.variable_adaptive_algorithm_0 = variable_adaptive_algorithm_0

    def get_taps(self):
        return self.taps

    def set_taps(self, taps):
        self.taps = taps

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps

    def get_access_key(self):
        return self.access_key

    def set_access_key(self, access_key):
        self.access_key = access_key




def main(top_block_cls=threading1, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

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
