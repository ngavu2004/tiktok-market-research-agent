from __future__ import annotations

from typing import Optional, Sequence

from crewai import Agent
from langchain_openai import ChatOpenAI

from src.tools import TikTokHashtagScrapeTool


def create_tiktok_researcher(
    *,
    llm: Optional[ChatOpenAI] = None,
    tools: Optional[Sequence[object]] = None,
    temperature: float = 0.0,
    model: str = "gpt-4o-mini",
) -> Agent:
    """Factory for a reusable TikTok researcher Agent.

    Parameters:
      - llm: Optional ChatOpenAI instance. If not provided, one is created.
      - tools: Optional custom tools. If not provided, uses TikTokHashtagScrapeTool().
      - temperature: Generation temperature for default LLM.
      - model: Model name for default LLM.
    """

    the_llm = llm or ChatOpenAI(model=model, temperature=temperature)
    the_tools = list(tools) if tools is not None else [TikTokHashtagScrapeTool()]

    return Agent(
        role="TikTok Research Analyst",
        goal=(
            "Turn trending business topics into effective TikTok hashtags, scrape the platform,"
            " and produce structured JSON with metadata, creator details, and content summaries."
        ),
        backstory=(
            "You specialize in social media trend analysis. You are precise with JSON and only"
            " include fields asked for."
        ),
        tools=the_tools,
        llm=the_llm,
        allow_delegation=False,
        verbose=False,
    )


# Optional ready-made instance with defaults for quick imports
tiktok_researcher: Agent = create_tiktok_researcher()