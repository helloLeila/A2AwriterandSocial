import unittest

import httpx

from backend.models.schemas import AnswererProfile
from backend.agents.demo_orchestrator import DemoOrchestrator, FastAnalysisAgent
from backend.services.zhihu_client import ZhihuClient


class DemoAnalysisQualityTest(unittest.IsolatedAsyncioTestCase):
    async def test_global_search_fetches_and_extracts_nested_items(self):
        seen_paths = []

        async def handler(request: httpx.Request) -> httpx.Response:
            seen_paths.append(request.url.path)
            return httpx.Response(
                200,
                json={
                    "data": {
                        "items": [
                            {
                                "title": "深度思考不是想得久",
                                "url": "https://www.zhihu.com/question/1/answer/2",
                            }
                        ]
                    }
                },
            )

        client = ZhihuClient(
            api_base="https://example.test/api",
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )

        results = await client.global_search("深度思考", limit=3)

        self.assertEqual(seen_paths, ["/api/v1/content/global_search"])
        self.assertEqual(results[0]["title"], "深度思考不是想得久")

    def test_answerer_profile_contains_angle_reference_links(self):
        profile = AnswererProfile(
            suitable_angle="从误区拆解切入，先指出多数人把深度思考误解成独处冥想，再给可练习的方法。",
            angle_reference_links=[
                "标题：深度思考不是想得久｜来源：知乎回答｜链接：https://www.zhihu.com/question/1/answer/2｜摘要：解释思考质量和时长的差别｜可借鉴：开头误区拆解｜风险：不要照搬案例"
            ],
        )

        self.assertIn("知乎回答", profile.angle_reference_links[0])

    def test_fast_agent_formats_result_items_as_reference_links(self):
        agent = FastAnalysisAgent()

        items = agent._format_result_items(
            [
                {
                    "title": "如何把深度思考练成日常习惯",
                    "author": "知乎用户",
                    "voteup_count": 1280,
                    "question_id": 11,
                    "answer_id": 22,
                    "excerpt": "这篇回答从误区、训练动作和复盘标准三个层面展开。",
                }
            ]
        )

        self.assertIn("https://www.zhihu.com/question/11/answer/22", items[0])
        self.assertIn("这篇回答从误区", items[0])

    def test_fallback_confusion_is_specific_not_title_rewrite(self):
        orchestrator = DemoOrchestrator()

        confusion = orchestrator._fallback_real_confusion("如何培养深度思考的能力？")

        self.assertNotIn("关于「如何培养深度思考的能力？」的真实困惑", confusion)
        self.assertIn("第一步", confusion)
        self.assertIn("判断标准", confusion)

    def test_reference_links_are_built_from_real_search_items(self):
        orchestrator = DemoOrchestrator()

        refs = orchestrator._build_reference_links(
            [
                {
                    "title": "深度思考如何开始",
                    "question_id": "123",
                    "answer_id": "456",
                    "excerpt": "回答讨论了初学者为什么看了很多方法仍然无法落地。",
                }
            ],
            fallback_question="如何培养深度思考的能力？",
        )

        self.assertIn("https://www.zhihu.com/question/123/answer/456", refs[0])
        self.assertIn("可借鉴", refs[0])


if __name__ == "__main__":
    unittest.main()
