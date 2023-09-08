import datetime
import pathlib
from threading import Thread, Event
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import mimetypes
import json
import socket


IP = "127.0.0.1"
WEB_PORT = 3000
SOCKET_PORT = 5000

BASE_DIR = pathlib.Path()
print(BASE_DIR.resolve())
STORAGE_FILE = "storage/data.json"


class HttpGetHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        self.save_data_to_json(data)
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)

        match pr_url.path:
            case '/':
                self.send_html_file(BASE_DIR.joinpath('index.html'))
            case '/message':
                self.send_html_file(BASE_DIR.joinpath('message.html'))
            case _:
                file = BASE_DIR.joinpath(pr_url.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html_file(BASE_DIR.joinpath('error.html'), 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        self.socket_client(data, IP, SOCKET_PORT)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def socket_client(self, data, ip, port):
        run_socket_client(data, ip, port)

    def send_static(self, file):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(file, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())


def save_data_to_json(data):
    data_parse = urllib.parse.unquote_plus(data.decode())
    data_parse = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
    storage_file = BASE_DIR.joinpath(STORAGE_FILE)
    if storage_file.exists():
        mode = "a"
    else:
        storage_file.parent.mkdir(parents=True, exist_ok=True)
        mode = "w"
    with open(storage_file, mode, encoding='utf-8') as fd:
        json.dump({str(datetime.datetime.now()): data_parse}, fd, ensure_ascii=False, indent=6)
        fd.write(",\n")


def run_web_server(server_class=HTTPServer, handler_class=HttpGetHandler, event=None):
    server_address = ("", WEB_PORT)
    http = server_class(server_address, handler_class)
    while not event.is_set():
        http.handle_request()

    print("end web")
    http.server_close()


def run_socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = IP, SOCKET_PORT
    sock.bind(server)
    while True:
        data, _ = sock.recvfrom(1024)
        if data == b"end":
            break
        save_data_to_json(data)

    print("end socket")
    sock.close()


def run_socket_client(data, ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server = ip, port
        sock.sendto(data, server)
        sock.close()


if __name__ == '__main__':

    event = Event()
    web_server_thread = Thread(target=run_web_server, args=(HTTPServer, HttpGetHandler, event))
    socket_server_thread = Thread(target=run_socket_server, args=())

    web_server_thread.start()
    socket_server_thread.start()

    while True:
        user_input = input("To end the the program type 'end' any time\n")
        if user_input.casefold() == "end":
            event.set()
            with urllib.request.urlopen(f"http://:{WEB_PORT}") as f:
                f.read(1)
            run_socket_client(b"end", IP, SOCKET_PORT)
            break

    web_server_thread.join()
    socket_server_thread.join()

    print("End program")
