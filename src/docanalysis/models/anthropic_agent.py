from typing import Any, Optional
import logging

import anthropic
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AnthropicAgent(BaseModel):
    """Anthropic Agent model using pydantic."""

    api_key: str = Field(default="", description="Anthropic API key")
    model: str = Field(
        default="claude-3-opus-20240229", description="Anthropic model to use"
    )
    client: Optional[Any] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Anthropic model."""
        if not self.client:
            raise ValueError("AnthropicAgent not initialized with API key")

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating text with Anthropic: {e}")
            raise
