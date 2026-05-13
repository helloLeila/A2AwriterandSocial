import json
import unittest

from backend.main import format_sse_event


class SSEEventTests(unittest.TestCase):
    def test_formats_named_event_with_json_payload(self):
        event = format_sse_event("strategy_ready", {"message": "ok"})

        self.assertTrue(event.startswith("event: strategy_ready\n"))
        self.assertTrue(event.endswith("\n\n"))

        data_line = next(line for line in event.splitlines() if line.startswith("data: "))
        payload = json.loads(data_line.removeprefix("data: "))

        self.assertEqual(payload["type"], "strategy_ready")
        self.assertEqual(payload["payload"], {"message": "ok"})
        self.assertIn("timestamp", payload)


if __name__ == "__main__":
    unittest.main()
