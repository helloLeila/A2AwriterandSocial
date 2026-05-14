import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKER_ORIGIN = "https://a2awriterandsocial2026.helloleila8h.workers.dev"


class ZeaburDeployConfigTest(unittest.TestCase):
    def test_root_dockerfile_is_ready_for_zeabur(self):
        dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("EXPOSE 80", dockerfile)
        self.assertIn("CMD [\"/app/start.sh\"]", dockerfile)
        self.assertIn("COPY --from=frontend-build /app/frontend/dist", dockerfile)

    def test_zeabur_env_template_uses_cloudflare_oauth_callback(self):
        env_path = REPO_ROOT / "backend" / ".env.zeabur.example"

        self.assertTrue(env_path.exists(), "backend/.env.zeabur.example should exist")

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

    def test_zeabur_secret_template_is_not_baked_into_docker_image(self):
        dockerignore = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8")
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertRegex(dockerignore, re.compile(r"(?m)^backend/\.env\*$"))
        self.assertRegex(dockerignore, re.compile(r"(?m)^!backend/\.env\.zeabur\.example$"))
        self.assertRegex(gitignore, re.compile(r"(?m)^backend/\.env\*$"))
        self.assertRegex(gitignore, re.compile(r"(?m)^!backend/\.env\.zeabur\.example$"))


if __name__ == "__main__":
    unittest.main()
