import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = REPO_ROOT / "frontend"


class CloudflareDeployConfigTest(unittest.TestCase):
    def test_worker_static_assets_publish_built_dist(self):
        config_path = FRONTEND_ROOT / "wrangler.toml"

        self.assertTrue(config_path.exists(), "frontend/wrangler.toml should exist")

        config = config_path.read_text(encoding="utf-8")
        self.assertRegex(config, r"(?m)^\s*directory\s*=\s*[\"']\./dist[\"']")
        self.assertRegex(
            config,
            r"(?m)^\s*not_found_handling\s*=\s*[\"']single-page-application[\"']",
        )
        self.assertRegex(config, r"(?m)^\s*binding\s*=\s*[\"']ASSETS[\"']")
        self.assertRegex(config, r"(?m)^\s*run_worker_first\s*=\s*\[\s*[\"']/api/\*[\"']\s*\]")

    def test_pages_static_redirects_do_not_proxy_assets_to_index(self):
        redirects_path = FRONTEND_ROOT / "public" / "_redirects"

        self.assertTrue(redirects_path.exists(), "frontend/public/_redirects should exist")

        redirects = redirects_path.read_text(encoding="utf-8")
        self.assertNotRegex(redirects, re.compile(r"/assets/\*\s+/index\.html"))
        self.assertRegex(redirects, re.compile(r"(?m)^/\*\s+/index\.html\s+200$"))

    def test_worker_proxies_api_requests_when_backend_is_configured(self):
        worker_path = FRONTEND_ROOT / "worker.js"

        self.assertTrue(worker_path.exists(), "frontend/worker.js should exist")

        worker = worker_path.read_text(encoding="utf-8")
        self.assertIn("API_BASE_URL", worker)
        self.assertIn("pathname.startsWith('/api/')", worker)
        self.assertIn("env.ASSETS.fetch(request)", worker)


if __name__ == "__main__":
    unittest.main()
