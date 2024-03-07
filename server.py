from http.server import BaseHTTPRequestHandler, HTTPServer
import re
import redis

mappings = {(r"^/books/(?P<book_id>\d+)$", "get_books"),
            (r"^/books/(?P<book_id>\d+)$", "get_books"),
            (r"^/$", "index")}

r = redis.StrictRedis(host="localhost", port=6379, db=0)

class WebRequestHandler(BaseHTTPRequestHandler):
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
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        # book_info = f"<h1> Info de libro {book_id} es correcto </h1>".encode("utf-8")
        book_info = r.get(f"book: {book_id}") or "No existe el libro".encode("utf-8")
        self.wfile.write(book_info)
 
    def index(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        index_page = f"<h1> Bienvenidos a los libros </h1>".encode("utf-8")
        self.wfile.write(index_page)

if __name__ == "__main__":
    print("Server starting...")
    server = HTTPServer(("0.0.0.0", 8000), WebRequestHandler)
    server.serve_forever()
