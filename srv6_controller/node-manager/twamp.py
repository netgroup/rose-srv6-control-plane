#!/usr/bin/python

from scapy.all import *




class TWAMPTestQuery(Packet):
    name = "TWAMPQuery"
    fields_desc=[IntField("SequenceNumber",0),
                    LongField("TransmitCounter",0),
                    BitEnumField("X",1,1,{0: "32bit Counter", 
                                          1: "64bit Counter"}),
                    BitEnumField("B",0,1,{0: "Packet Counter", 
                                          1: "Octet Counter"}),
                    BitField("MBZ",0,6),
                    ByteField("BlockNumber",0),
                    ShortField("MBZ",0),
                    ThreeBytesField("MBZ",0),
                    ByteEnumField("SenderControlCode", 0, {0: "Out-of-band Response Requested",
                                                           1: "In-band Response Requested"})
                    ] #manca il padding
 

class TWAMPTestResponse(Packet):
    name = "TWAMPResponse"
    fields_desc=[IntField("SequenceNumber",0),
                    LongField("TransmitCounter",0),
                    BitField("X",0,1),
                    BitField("B",0,1),
                    BitField("MBZ",0,6),
                    XByteField("BlockNumber",0),
                    ShortField("MBZ",0),
                    LongField("ReceiveCounter",0),
                    IntField("SenderSequenceNumber",0),
                    LongField("SenderCounter",0),
                    BitField("X2",0,1),
                    BitField("B2",0,1),
                    BitField("MBZ",0,6),
                    XByteField("SenderBlockNumber",0),
                    XByteField("MBZ",0),
                    ByteEnumField("ReceverControlCode", 0, {1: "Error - Invalid Message"}),
                    XByteField("SenderTTL",0)] #manca il padding