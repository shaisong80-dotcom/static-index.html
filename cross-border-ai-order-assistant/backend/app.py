from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ai_advisor import build_advice
from rules import analyze_orders, load_sample_orders, parse_csv


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
SAMPLE = Path(__file__).resolve().parent / "sample_orders.csv"


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(404)
            return
        content_type = "text/html; charset=utf-8"
        if path.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif path.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        self._send_json({})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/orders":
            result = analyze_orders(load_sample_orders(str(SAMPLE)))
            self._send_json(result)
            return
        if parsed.path == "/api/advice":
            order_id = parse_qs(parsed.query).get("order_id", [""])[0]
            result = analyze_orders(load_sample_orders(str(SAMPLE)))
            order = next((item for item in result["orders"] if item["order_id"] == order_id), None)
            if not order:
                self._send_json({"error": "order not found"}, 404)
                return
            self._send_json(build_advice(order))
            return

        file_path = FRONTEND / "index.html" if parsed.path == "/" else FRONTEND / parsed.path.lstrip("/")
        self._send_file(file_path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/analyze":
            self._send_json({"error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8-sig")
        try:
            orders = parse_csv(body)
            self._send_json(analyze_orders(orders))
        except Exception as exc:
            self._send_json({"error": str(exc)}, 400)


if __name__ == "__main__":
    port = 8765
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Cross-border AI order assistant running at http://127.0.0.1:{port}")
    server.serve_forever()
