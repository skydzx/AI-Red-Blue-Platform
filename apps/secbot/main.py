"""SecBot-AI application entry point."""

import asyncio
from typing import Optional
from datetime import datetime, timezone

from ai_red_blue_common import get_settings, get_logger
from ai_red_blue_ai import (
    AIProvider,
    ProviderConfig,
    OpenAIProvider,
    ChatMessage,
    ChatRole,
)
from ai_red_blue_core import (
    AlertManager,
    Alert,
    AlertSeverity,
    AlertType,
)


settings = get_settings()
logger = get_logger("secbot")


class SecBotAI:
    """SecBot-AI: AI-powered security assistant."""

    def __init__(self):
        self.alert_manager = AlertManager()
        self.ai_provider: Optional[AIProvider] = None

    async def initialize(self):
        """Initialize SecBot."""
        config = ProviderConfig(
            type="openai",
            name="openai",
            api_key=settings.openai_api_key,
        )
        self.ai_provider = OpenAIProvider(config)
        logger.info("SecBot-AI initialized")

    async def analyze_alert(self, alert: Alert) -> dict:
        """Analyze an alert using AI."""
        messages = [
            ChatMessage(
                role=ChatRole.SYSTEM,
                content="You are a security analyst assistant. Analyze the following alert and provide recommendations.",
            ),
            ChatMessage(
                role=ChatRole.USER,
                content=f"Analyze this alert:\nTitle: {alert.title}\nDescription: {alert.description}\nSeverity: {alert.severity}\nType: {alert.type}",
            ),
        ]

        response = await self.ai_provider.chat(messages)

        return {
            "analysis": response.content,
            "confidence": response.metadata.get("confidence", 0.0),
            "recommendations": [],  # Parse from response
        }

    async def generate_response(
        self,
        alert: Alert,
        context: Optional[dict] = None,
    ) -> str:
        """Generate response recommendations for an alert."""
        messages = [
            ChatMessage(
                role=ChatRole.SYSTEM,
                content="Provide actionable response recommendations for this security alert.",
            ),
            ChatMessage(
                role=ChatRole.USER,
                content=f"Alert: {alert.title}\n\nContext: {context or 'No additional context'}",
            ),
        ]

        response = await self.ai_provider.chat(messages)
        return response.content

    async def chat(self, user_message: str) -> str:
        """Interactive chat with SecBot."""
        messages = [
            ChatMessage(role=ChatRole.USER, content=user_message),
        ]

        response = await self.ai_provider.chat(messages)
        return response.content

    async def run(self):
        """Run SecBot main loop."""
        logger.info("SecBot-AI starting...")
        await self.initialize()

        while True:
            await asyncio.sleep(60)
            # Check for new alerts and analyze them
            logger.info("Checking for new alerts...")


async def main():
    """Main entry point."""
    bot = SecBotAI()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
