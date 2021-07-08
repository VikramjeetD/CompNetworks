import socket

SERVER_ADDRESS = socket.gethostbyname(socket.gethostname())
CLIENT_ADDRESS = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 50051
CLIENT_PORT = 50003

CHUNK_SIZE = 2 ** 10
DATA_SIZE = 2 ** 10
HEADER_SIZE = 9
WINDOW_SIZE = 10

SEND_TIMEOUT = 0.5
SYN_WAIT = 0.5
FIN_WAIT = 5
FINACK_WAIT = 2

