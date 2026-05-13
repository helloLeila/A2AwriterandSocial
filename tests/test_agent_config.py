import unittest

from backend.agents.base import AgentConfig


class AgentConfigTest(unittest.TestCase):
    def test_agent_config_ignores_non_agent_env_values(self):
        config = AgentConfig()

        self.assertIsInstance(config.anthropic_api_key, str)

    def test_agent_config_accepts_anthropic_compatible_base_url(self):
        config = AgentConfig(
            anthropic_api_key="kimi-key",
            anthropic_base_url="https://api.kimi.com/coding/",
            model_name="kimi-for-coding",
        )

        self.assertEqual(config.anthropic_base_url, "https://api.kimi.com/coding/")
        self.assertEqual(config.model_name, "kimi-for-coding")


if __name__ == "__main__":
    unittest.main()
