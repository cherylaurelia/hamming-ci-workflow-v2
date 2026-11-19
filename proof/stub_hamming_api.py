"""Stub of the Hamming REST endpoints the CI workflow calls (proof only, no real calls).

Payload shape copies the fixtures in tests/test_check_results.py, which Hamming wrote
for the current REST API (PR #3). The agent_id picks the scenario: pass, fail, timeout.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

RUNS = {}

def case(i, status="COMPLETED"):
    return {"id": f"case-run-{i}", "testCaseId": f"case-{i}", "status": status, "assertionResults": []}

def results(run_id, scenario):
    if scenario in ("fail", "runfailed"):
        cases, failed, score = [case(1), case(2), case(3), case(4, "ERROR")], 1, 62.5
    else:
        cases, failed, score = [case(1), case(2), case(3), case(4)], 0, 100.0
    return {
        "summary": {
            "id": run_id, "status": "FAILED" if scenario == "runfailed" else "COMPLETED",
            "stats": {"total": len(cases), "completed": len(cases), "cancelled": 0, "failed": failed, "pending": 0},
            "assertions": {"overallScore": score, "categories": [{"name": "General", "score": score,
                           "status": "passed" if score >= 100 else "failed", "assertionIds": ["a-1"]}]},
        },
        "results": cases,
        "resultsUrl": f"https://app.hamming.ai/test-runs/{run_id}",
    }

class H(BaseHTTPRequestHandler):
    def send(self, body, code=200):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        scenario = body["agentId"]
        run_id = f"stub-{scenario}"
        RUNS[run_id] = scenario
        self.send({"testRunId": run_id, "resultsUrl": f"https://app.hamming.ai/test-runs/{run_id}", "status": "RUNNING"})

    def do_GET(self):
        parts = self.path.strip("/").split("/")  # test-runs/<id>/<status|results>
        run_id, kind = parts[-2], parts[-1]
        scenario = RUNS.get(run_id, "pass")
        if kind == "status":
            self.send({"status": {"timeout": "RUNNING", "runfailed": "FAILED"}.get(scenario, "COMPLETED")})
        else:
            self.send(results(run_id, scenario))

    def log_message(self, fmt, *args):
        print("stub:", fmt % args, flush=True)

HTTPServer(("127.0.0.1", 8787), H).serve_forever()
