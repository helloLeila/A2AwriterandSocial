import unittest

from backend.main import format_flow_error


class FlowErrorMessageTest(unittest.TestCase):
    def test_formats_llm_authentication_errors(self):
        error = Exception("Error code: 401 - {'message': 'invalid x-api-key'}")

        message = format_flow_error(error)

        self.assertEqual(
            message,
            "LLM API Key 无效或未配置，请检查 backend/.env 中的 ANTHROPIC_API_KEY、ANTHROPIC_BASE_URL 和 MODEL_NAME 后重试。",
        )


if __name__ == "__main__":
    unittest.main()
