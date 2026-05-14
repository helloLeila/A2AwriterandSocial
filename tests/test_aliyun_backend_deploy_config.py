import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKER_ORIGIN = "https://a2awriterandsocial2026.helloleila8h.workers.dev"


class AliyunBackendDeployConfigTest(unittest.TestCase):
    def test_compose_exposes_backend_http_port_for_cloudflare_proxy(self):
        compose_path = REPO_ROOT / "docker-compose.aliyun.yml"

        self.assertTrue(compose_path.exists(), "docker-compose.aliyun.yml should exist")

        compose = compose_path.read_text(encoding="utf-8")
        self.assertIn("./backend/.env.aliyun", compose)
        self.assertRegex(compose, re.compile(r"\$\{A2A_PUBLIC_PORT:-18080\}:80"))
        self.assertIn("restart: unless-stopped", compose)

    def test_aliyun_env_template_uses_cloudflare_oauth_callback(self):
        env_path = REPO_ROOT / "backend" / ".env.aliyun.example"

        self.assertTrue(env_path.exists(), "backend/.env.aliyun.example should exist")

        env = env_path.read_text(encoding="utf-8")
        self.assertIn("APP_ENV=production", env)
        self.assertIn(f"CORS_ORIGINS={WORKER_ORIGIN}", env)
        self.assertIn(
            f"ZHIHU_OAUTH_REDIRECT_URI={WORKER_ORIGIN}/api/auth/zhihu/callback",
            env,
        )
        self.assertIn("ZHIHU_OAUTH_SUCCESS_REDIRECT=/", env)
        self.assertIn("ANTHROPIC_API_KEY=", env)
        self.assertIn("ANTHROPIC_BASE_URL=", env)
        self.assertIn("MODEL_NAME=", env)
        self.assertNotIn("sk-", env)

    def test_local_secret_env_files_are_ignored_by_git_and_docker(self):
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        dockerignore = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8")

        self.assertRegex(gitignore, re.compile(r"(?m)^backend/\.env\*$"))
        self.assertRegex(gitignore, re.compile(r"(?m)^!backend/\.env\.aliyun\.example$"))
        self.assertRegex(dockerignore, re.compile(r"(?m)^backend/\.env\*$"))
        self.assertRegex(dockerignore, re.compile(r"(?m)^!backend/\.env\.aliyun\.example$"))


if __name__ == "__main__":
    unittest.main()
