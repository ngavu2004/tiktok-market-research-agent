from crewai import Agent
from src.tools import TikTokHashtagScrapeTool

researcher = Agent(
        role="TikTok Research Analyst",
        goal=(
            "Turn trending business topics into effective TikTok hashtags, scrape the platform,"
            " and produce structured JSON with metadata, creator details, and content summaries."
        ),
        backstory=(
            "You specialize in social media trend analysis. You are precise with JSON and only"
            " include fields asked for."
        ),
        tools=[scrape_tool],
        llm=llm,
        allow_delegation=False,
        verbose=False,
    )