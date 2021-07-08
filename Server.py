import socket
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor as Pool
from Packet import create_packet, decode_header, Packet
from Constants import SERVER_PORT, CHUNK_SIZE, DATA_SIZE, SERVER_ADDRESS, HEADER_SIZE, WINDOW_SIZE, SEND_TIMEOUT, FINACK_WAIT
from pathlib import Path
import math


def send_with_timeout(s, data, address, left_seq, seq_no, acked):
    # print(f'SENDING...{decode_header(data[:HEADER_SIZE]).seq_no, data[HEADER_SIZE:]}')
    s.sendto(data, address)
    while not acked[seq_no]:
        time.sleep(0.1)


def send_chunk(s, data, address, seq_no, left_seq, acked):
    while not acked[seq_no]:
        ptimeout = multiprocessing.Process(target=send_with_timeout, args=(s, data, address, left_seq, seq_no, acked))
        ptimeout.start()
        ptimeout.join(SEND_TIMEOUT)
        ptimeout.terminate()


def receive(s, left_seq, acked):
    while True:
        header, _ = s.recvfrom(CHUNK_SIZE)
        header = decode_header(header[:HEADER_SIZE])
        if header.pkt_type == Packet.ACK:
            # print(f'Received: {header.seq_no}')
            acked[header.seq_no] = True
            left_seq[0] += 1


def finack_wait(ss, recv_fin):
    header, address = ss.recvfrom(CHUNK_SIZE)
    header = decode_header(header[:HEADER_SIZE])
    if header.pkt_type == Packet.ACK:
        recv_fin[0] = True


def send_file(ss, left_seq, acks):
    # Wait for a SYN packet
    header, address = ss.recvfrom(CHUNK_SIZE)
    header = decode_header(header[:HEADER_SIZE])
    if header.pkt_type == Packet.SYN:
        packets = []
        # Start sending packets asynchronously, upper bounded by window size (max pool size)
        with open('File.txt', 'rb') as file:
            s_no = 0
            while True:
                chunk = file.read(DATA_SIZE)
                if not chunk:
                    break
                packet = create_packet(data=chunk, seq_no=s_no)
                packets.append(packet)
                s_no += 1
        rproc = multiprocessing.Process(target=receive, args=(ss, left_seq, acks))
        rproc.start()
        with Pool(max_workers=WINDOW_SIZE) as send_pool:
            for i, packet in enumerate(packets):
                time.sleep(0.05)
                send_pool.submit(send_chunk, ss, packet, address, i, left_seq, acks)
        while left_seq[0] < len(packets):
            time.sleep(0.1)
        rproc.terminate()
        i = 0

        # Handle FINACK
        while True:
            i += 1
            fin_packet = create_packet(Packet.FIN)
            ss.sendto(fin_packet, address)
            recv_finack = multiprocessing.Manager().list()
            recv_finack.append(False)
            pfinack = multiprocessing.Process(target=finack_wait, args=(ss, recv_finack))
            pfinack.start()
            pfinack.join(FINACK_WAIT)
            pfinack.terminate()
            if recv_finack[0] or i > 20:
                break
        return


if __name__ == '__main__':
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serversocket.bind((SERVER_ADDRESS, SERVER_PORT))
    manager = multiprocessing.Manager()
    left_seq_no = manager.list()
    left_seq_no.append(0)
    window_acks = manager.list()
    window_acks += [False for _ in range(math.ceil(Path('File.txt').stat().st_size / DATA_SIZE))]

    # Start process for sending file
    psend = multiprocessing.Process(target=send_file, args=(serversocket, left_seq_no, window_acks))

    psend.start()
    psend.join()
    psend.terminate()
    serversocket.close()
