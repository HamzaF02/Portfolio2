'''
    #Utility functions: 1) to create a packet of 1472 bytes with header (12 bytes) (sequence number, acknowledgement number,
    #flags and receiver window) and applicaton data (1460 bytes), and 2) to parse
    # the extracted header from the application data.
'''

from struct import *

# I integer (unsigned long) = 4bytes and H (unsigned short integer 2 bytes)
# see the struct official page for more info

header_format = '!IIHH'

# 0                   1                   2                   3
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                        Sequence Number                        |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                     Acknowledgment Number                     |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |           Flags               |           Window              |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                                                               |
# +                          Message Body                         +
# |                                                               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

# print the header size: total = 12
# print(f'size of the header = {calcsize(header_format)}')


def create_packet(seq, ack, flags, win, data):

    header = pack(header_format, seq, ack, flags, win)
    print(header)

    packet = header + data

    # print(f'packet containing header + data of size {len(packet)}')
    return packet


def parse_header(header):

    header_from_msg = unpack(header_format, header)

    return header_from_msg


def parse_flags(flags):

    syn = flags & (1 << 3)
    ack = flags & (1 << 2)
    fin = flags & (1 << 1)
    return syn, ack, fin


s = create_packet(1, 0, 2, 0, b'0'*100)

w = parse_header(s[:12])
print(w, s[12:].decode())
print(parse_flags(w[2]))


# # now let's create a packet with sequence number 1
# print('\n\ncreating a packet')

# data = b'0' * 1460
# print(f'app data for size ={len(data)}')

# sequence_number = 1
# acknowledgment_number = 0
# window = 0  # window value should always be sent from the receiver-side
# flags = 0  # we are not going to set any flags when we send a data packet

# # msg now holds a packet, including our custom header and data
# msg = create_packet(sequence_number, acknowledgment_number,
#                     flags, window, data)
# # print(msg)

# # now let's look at the header
# # we already know that the header is in the first 12 bytes

# header_from_msg = msg[:12]
# print(len(header_from_msg))

# # now we get the header from the parse_header function
# # which unpacks the values based on the header_format that
# # we specified
# seq, ack, flags, win = parse_header(header_from_msg)
# print(f'seq={seq}, ack={ack}, flags={flags}, recevier-window={win}')

# # let's extract the data_from_msg that holds
# # the application data of 1460 bytes
# data_from_msg = msg[12:]
# print(len(data_from_msg))


# # let's mimic an acknowledgment packet from the receiver-end
# # now let's create a packet with acknowledgement number 1
# # an acknowledgment packet from the receiver should have no data
# # only the header with acknowledgment number, ack_flag=1, win=6400
# data = b''
# print('\n\nCreating an acknowledgment packet:')
# print(f'this is an empty packet with no data ={len(data)}')

# sequence_number = 0
# acknowledgment_number = 1  # an ack for the last sequnce
# window = 0  # window value should always be sent from the receiver-side

# # let's look at the last 4 bits:  S A F R
# # 0 0 0 0 represents no flags
# # 0 1 0 0  ack flag set, and the decimal equivalent is 4
# flags = 4

# msg = create_packet(sequence_number, acknowledgment_number,
#                     flags, window, data)
# print(f'this is an acknowledgment packet of header size={len(msg)}')

# # let's parse the header
# # it's an ack message with only the header
# seq, ack, flags, win = parse_header(msg)
# print(f'seq={seq}, ack={ack}, flags={flags}, receiver-window={win}')

# # now let's parse the flag field
# syn, ack, fin = parse_flags(flags)
# print(f'syn_flag = {syn}, fin_flag={fin}, and ack_flag={ack}')
