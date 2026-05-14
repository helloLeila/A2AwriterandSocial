import unittest

from fastapi.testclient import TestClient

from backend.main import app


class ZhihuAuthRoutesTest(unittest.TestCase):
    def test_login_redirects_to_zhihu_authorize(self):
        client = TestClient(app)

        response = client.get("/api/auth/zhihu/login", follow_redirects=False)

        self.assertEqual(response.status_code, 307)
        self.assertTrue(response.headers["location"].startswith("https://openapi.zhihu.com/authorize?"))
        self.assertIn("response_type=code", response.headers["location"])

    def test_me_returns_logged_out_without_cookie(self):
        client = TestClient(app)

        response = client.get("/api/auth/zhihu/me")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"logged_in": False})


if __name__ == "__main__":
    unittest.main()
