from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List

from .engine import search_venues
from .models import DietaryTag, SearchRequest
from .sample_data import SAMPLE_VENUES


def _parse_search_request(payload: Dict) -> SearchRequest:
    required_tags = {DietaryTag(item) for item in payload.get("required_tags", [])}
    excluded_allergens = set(payload.get("excluded_allergens", []))
    return SearchRequest(required_tags=required_tags, excluded_allergens=excluded_allergens)


def _serialize_results(results) -> List[Dict]:
    return [
        {
            "id": result.venue.id,
            "name": result.venue.name,
            "supported_tags": sorted(tag.value for tag in result.venue.supported_tags),
            "allergens_present": sorted(result.venue.allergens_present),
            "trust_score": result.trust_score,
            "reasons": result.reasons,
        }
        for result in results
    ]


class DietaryRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, body: Dict) -> None:
        body_bytes = json.dumps(body).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"ok": True})
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/search":
            self._send_json(404, {"error": "Not found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload_bytes = self.rfile.read(length)

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
            request = _parse_search_request(payload)
            profile_name = payload.get("profile", "balanced")
            results = search_venues(SAMPLE_VENUES, request, profile_name=profile_name)
            self._send_json(200, {"results": _serialize_results(results)})
        except Exception as exc:
            self._send_json(400, {"error": str(exc)})


def run_server(port: int = 8000) -> None:
    server = HTTPServer(("0.0.0.0", port), DietaryRequestHandler)
    print(f"Server running on http://localhost:{port}")
    server.serve_forever()
