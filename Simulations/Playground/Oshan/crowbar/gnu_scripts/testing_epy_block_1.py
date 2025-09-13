"""
Embedded Python Block: File Source to Tagged Stream
"""

import numpy as np
from gnuradio import gr
import time
import pmt
import os.path
import sys
import base64
import struct

"""
State definitions
    0   idle
    1   send preamble
    2   send file data
"""

class blk(gr.sync_block):
    def __init__(self, FileName='None', Pkt_len=52):
        gr.sync_block.__init__(
            self,
            name='EPB: File Source to Tagged Stream',
            in_sig=None,
            out_sig=[np.uint8])
        self.FileName = FileName
        self.Pkt_len = Pkt_len
        self.state = 0      
        self.indx = 0
        self._debug = 0     
        self.data = ""
        self.address = 0xC001D00D           #address 
        self.seq_num = 0                    #seq number of packet being sent
        self.sync_word = b'%SYNC%'          #syncword to denote start of packet
        self.crc = 0
        self.poly = 0x104C11DB7
        n_bytes = 32                        #length of in-packet preamble

        if (os.path.exists(self.FileName)):
            # open input file
            self.f_in = open (self.FileName, 'rb')
            self._eof = False
            if (self._debug):
                print ("File name:", self.FileName)
            self.state = 1
        else:
            print(self.FileName, 'does not exist')
            self._eof = True
            self.state = 0

        #preamble consists of 01 repeating n times
        self.char_list = bytes([0x55]) * n_bytes
        self.c_len = len (self.char_list)
        if (self._debug):
            print ("Length of Preamble: ", self.c_len)

    #will continously be looped by GNU
    def work(self, input_items, output_items):

        #we can probably have a conditional here to check if the file is True or Not
        #if its still waiting for ACK will go to state 0

        if (self.state == 0):
            # idle state
            self.seq_num=0
            if (self._debug):
                print("State: 0")
            return (0)

        elif (self.state == 1):
            # send preamble state
            if (self._debug):
                print("State: 1")
            key1 = pmt.intern("packet_len")
            val1 = pmt.from_long(self.c_len)
            self.add_item_tag(0,    # Write to output port 0
                self.indx,          # Index of the tag
                key1,               # Key of the tag
                val1                # Value of the tag
                )
            self.indx += self.c_len
            i = 0
            while (i < self.c_len):
                output_items[0][i] = self.char_list[i]
                i += 1
            #changing to state 2 after sending one preamble of n length
            self.state = 2      
            return (self.c_len)

        elif (self.state == 2):
            # send message packet state
            while (not (self._eof)):

                #needs to be edited to read from the queue

                buff = self.f_in.read (self.Pkt_len)
                b_len = len(buff)
                if b_len == 0:
                    print ('End of file')
                    self._eof = True
                    self.f_in.close()
                    self.state = 3      
                    self.pre_count = 0
                    break
                #crc generation
                data = int.from_bytes(buff, byteorder='big')
                data <<= 32
                poly_length = self.poly.bit_length()
                while data.bit_length() >= poly_length:
                    data ^= self.poly << (data.bit_length() - poly_length)
                #crc is 32 bit fixed length
                self.crc = data.to_bytes(4, byteorder='big')
                encoded = buff
                #header generation, H = 2 bytes; I = 4 bytes;
                self.header = struct.pack(">H I I", self.seq_num, self.address, len(encoded))
                prepend = self.sync_word + self.header
                encoded = prepend + encoded + self.crc
                e_len = len(encoded)
                self.seq_num+=1
                if (self._debug):
                    print ('b64 length =', e_len)
                key0 = pmt.intern("packet_len")
                val0 = pmt.from_long(e_len)
                self.add_item_tag(0,    # Write to output port 0
                    self.indx,          # Index of the tag
                    key0,               # Key of the tag
                    val0                # Value of the tag
                    )
                self.indx += e_len
                i = 0
                while (i < e_len):
                    output_items[0][i] = encoded[i]
                    i += 1
                #changing the state to 1, to resend preamble again after a packet is sent
                self.state = 1
                return (e_len)

        return (0)


