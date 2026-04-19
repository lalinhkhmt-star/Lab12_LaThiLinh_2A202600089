"""
Mock LLM used for the Day 12 lab.
No external API key required.
"""
from __future__ import annotations

import random
import time

MOCK_RESPONSES = {
    "default": [
        "Đây là câu trả lời từ AI agent mock. Bản production có thể thay bằng OpenAI hoặc Anthropic.",
        "Agent đang chạy ổn định trong môi trường production giả lập.",
        "Yêu cầu đã được xử lý thành công bởi production agent.",
    ],
    "docker": [
        "Docker giúp đóng gói ứng dụng cùng dependencies để chạy nhất quán giữa máy local và production."
    ],
    "deploy": [
        "Deployment là quá trình đưa ứng dụng từ môi trường phát triển lên hệ thống phục vụ người dùng thật."
    ],
    "redis": [
        "Redis phù hợp để lưu session, rate limit, budget usage và conversation history dùng chung giữa nhiều instances."
    ],
}


def ask(question: str, delay: float = 0.05) -> str:
    time.sleep(delay + random.uniform(0, 0.05))
    lowered = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in lowered:
            return random.choice(responses)
    return random.choice(MOCK_RESPONSES["default"])
