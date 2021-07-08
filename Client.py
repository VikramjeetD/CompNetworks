import socket
import multiprocessing
import time
from Packet import create_packet, decode_header, Packet
from Constants import SERVER_PORT, CLIENT_PORT, CHUNK_SIZE, SERVER_ADDRESS, CLIENT_ADDRESS, \
    HEADER_SIZE, SYN_WAIT, FIN_WAIT
from time import perf_counter_ns
from pathlib import Path


def receive(cs, has_response, data, server_address):
    """
    Receive a single packet
    """
    while True:
        # Receive a packet, and decode header, and extract the data
        packet, _ = cs.recvfrom(CHUNK_SIZE)
        header = decode_header(packet[:HEADER_SIZE])
        if header.pkt_type == Packet.DATA:
            # print(header.seq_no)
            has_response[0] = 1
            data[header.seq_no] = packet[HEADER_SIZE:]
            ack_packet = create_packet(Packet.ACK, header.seq_no)
            cs.sendto(ack_packet, server_address)
        # When a FIN packet is received, all DATA packets have been ACKd at the server
        elif header.pkt_type == Packet.FIN:
            # print('Got FIN')
            break


def receive_dup_fin(cs, server_address, dup_fin):
    """
    Handle duplicate FINs
    """
    # print('Waiting dup FIN')
    header, _ = cs.recvfrom(CHUNK_SIZE)
    header = decode_header(header[:HEADER_SIZE])
    if header.pkt_type == Packet.FIN:
        # print('Got dup FIN')
        dup_fin[0] = True
        ack_packet = create_packet(Packet.ACK)
        cs.sendto(ack_packet, server_address)


def get_file(cs, server_address, has_response, data):
    """
    Function to get a file from the server
    """
    start = perf_counter_ns()
    # Start process for receiving packets
    rproc = multiprocessing.Process(target=receive, args=(cs, has_response, data, server_address))
    rproc.start()
    # Send SYN packet to setup connection, resend SYN unless it starts receiving DATA packets
    while True:
        syn_packet = create_packet(Packet.SYN)
        cs.sendto(syn_packet, server_address)
        # print(syn_packet)
        time.sleep(SYN_WAIT)
        if has_response[0]:
            break
    rproc.join() # Receive the whole file
    end = perf_counter_ns()
    print('File size: ', Path('File.txt').stat().st_size)
    print('Time taken: ', ((end - start) / 1000000000))
    print('Throughput: ', Path('File.txt').stat().st_size / ((end - start) / 1000000000), ' b/s')

    # Respond to FIN packet, resent ACK on receiving duplicate FINs
    dup_fin = multiprocessing.Manager().list()
    dup_fin.append(False)
    ack_packet = create_packet(Packet.ACK)
    cs.sendto(ack_packet, server_address)
    i = 0
    while i < 20:
        i += 1
        dup_fin[0] = False
        finproc = multiprocessing.Process(target=receive_dup_fin, args=(cs, server_address, dup_fin))
        finproc.start()
        finproc.join(FIN_WAIT)
        finproc.terminate()
        if not dup_fin[0]:
            break

    # Write file to disk
    with open('Opfileclient.txt', 'wb') as opFile:
        for d in range(len(data)):
            opFile.write(data[d])


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((CLIENT_ADDRESS, CLIENT_PORT))

    # Create a manager to handle the multiple processes while receiving
    manager = multiprocessing.Manager()
    has_resp = manager.list()
    has_resp.append(False)
    data_list = manager.dict()
    precv = multiprocessing.Process(target=get_file, args=(s, (SERVER_ADDRESS, SERVER_PORT), has_resp, data_list))

    precv.start()
    precv.join()
    s.close()
