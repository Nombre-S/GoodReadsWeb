from http.server import BaseHTTPRequestHandler, HTTPServer
import re
import redis
from http.cookies import SimpleCookie
import uuid
from urllib.parse import parse_qsl, urlparse

mappings = {
        (r"^/books/(?P<book_id>\d+)$", "get_books"),
        (r"^/$", "index"),
        (r"^/search", "search")
        }

r = redis.StrictRedis(host="localhost", port=6379, db=0)

class WebRequestHandler(BaseHTTPRequestHandler):
     
    @property
    def url(self):
        return urlparse(self.path)

    @property 
    def query_data(self):
        return dict(parse_qsl(self.url.query))

    def search(self):
        query_key = self.query_data.get('q')
        if query_key:
            html_content = r.get(query_key)
            if html_content:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html_content)
                return

        self.send_response(404)
        self.end_headers()
        error_message = "<h1>La clave no existe o no se proporcionó.</h1>"
        self.wfile.write(error_message.encode("utf-8"))

    def cookies(self):
        return SimpleCookie(self.headers.get("Cookie"))

    def get_session(self):
        cookies = self.cookies()
        session_id = None
        if not cookies:
            session_id = uuid.uuid4()
        else:
            session_id = cookies["session_id"].value
        return session_id
            
    def write_session_cookie(self, session_id):
        cookies = SimpleCookie()
        cookies["session_id"] = session_id
        cookies["session_id"]["max-age"] = 1000
        self.send_header("Set-Cookie", cookies.output(header=""))

    def do_GET(self):
        self.url_mapping_response()

    def url_mapping_response(self):
        for pattern, method in mappings:
            match = self.get_params(pattern, self.path)
            if match is not None:
                md = getattr(self, method)
                md(**match)
                return

        self.send_response(404)
        # self.send_header("Content-Type", "text/html")
        self.end_headers()
        error = f"<h1> Not found </h1>".encode("utf-8")
        self.wfile.write(error)

    def get_params(self, pattern, path):
        match = re.match(pattern, path)
        if match:
            return match.groupdict()

    def get_books(self, book_id):
        session_id = self.get_session()
        r.lpush(f"session: {session_id}", f"book: {book_id}")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.write_session_cookie(session_id)
        self.end_headers()
        book_info = r.get(f"book: {book_id}") or "<h1> No existe el libro </h1>".encode("utf-8")
        self.wfile.write(book_info)
        self.wfile.write(f"session: {session_id}".encode("utf-8"))
        book_list = r.lrange(f"session: {session_id}", 0, 1)
        for book in book_list:
            self.wfile.write(f" book: {book}".encode("utf-8"))
    
   
    def index(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        with open('html/index.html') as f:
            response = f.read()
        self.wfile.write(response.encode("utf-8"))

if __name__ == "__main__":
    print("Server starting...")
    server = HTTPServer(("0.0.0.0", 8000), WebRequestHandler)
    server.serve_forever()
