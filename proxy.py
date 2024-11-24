import sys
import socket
import threading

# Create a filter to replace non-printable characters with '.'
HEX_FILTER = ''.join([(len(repr(chr(i))) == 3) and chr(i) or '.' for i in range(256)])

# Function to generate a hex dump of the input data
def hexdump(src, length=16, show=True):
    if isinstance(src, bytes):
        src = src.decode()
    results = []
    for i in range(0, len(src), length):
        word = str(src[i:i+length])
        printable = word.translate(HEX_FILTER)  # Make characters printable
        hexa = ' '.join([f'{ord(c):02X}' for c in word])  # Convert to hex
        hexwidth = length * 3  # Format for hex alignment
        results.append(f'{i:04x} {hexa:<{hexwidth}} {printable}')
    if show:
        for line in results:
            print(line)
    else:
        return results

# Function to receive data from a socket
def receive_from(connection):
    buffer = b"" 
    connection.settimeout(5)
    try:
        while True:
            data = connection.recv(4096)
            if not data:  # Stop if no data received
                break
            buffer += data  # Append received data to the buffer
    except:
        pass
    return buffer

# Function to modify requests before sending to the remote host
def request_handler(buffer):
    
    return buffer

# Function to modify responses before sending back to the client
def response_handler(buffer):
    
    return buffer

# Function to handle proxy logic between client and remote server
def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    # Connect to the remote server
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    if receive_first:  # Optionally receive data from the remote server first
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)
        remote_buffer = response_handler(remote_buffer)  # Modify response if needed
        if len(remote_buffer):
            client_socket.send(remote_buffer)

    while True:
        # Receive data from the client
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            print(f"[==>] Received {len(local_buffer)} bytes from localhost.")
            hexdump(local_buffer)
            local_buffer = request_handler(local_buffer)  # Modify request if needed
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote")

        # Receive data from the remote server
        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print(f"[<==] Received {len(remote_buffer)} bytes from remote.")
            hexdump(remote_buffer)
            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[<==] Sent to localhost")

        # Close connections if no more data
        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connection.")
            break

# Function to start the proxy server and handle incoming connections
def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((local_host, local_port))  # Bind to the specified address and port
    except:
        print("[!!] Failed to bind. Check permissions or other sockets.")
        sys.exit(0)

    print(f"[*] Listening on {local_host}:{local_port}")
    server.listen(5)  # Start listening for connections (up to 5 queued)
    while True:
        client_socket, addr = server.accept()
        print(f"[>] Connection from {addr[0]}:{addr[1]}")

        # Start a new thread to handle the connection
        proxy_thread = threading.Thread(
            target=proxy_handler,
            args=(client_socket, remote_host, remote_port, receive_first)
        )
        proxy_thread.start()

# Entry point of the script
def main():
    # Check if all required arguments are provided
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [localhost] [localport] [remotehost] [remoteport] [receive_first]")
        sys.exit(0)

    # Extract arguments
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])
    receive_first = sys.argv[5] == "True"

    # Start the server loop
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)

if __name__ == '__main__':
    main()
