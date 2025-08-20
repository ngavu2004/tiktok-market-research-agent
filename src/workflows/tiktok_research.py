from __future__ import annotations

from typing import Any, Dict, List, Optional
import os
import json

from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

from src.tools import TikTokHashtagScrapeTool


def create_search_query_crew(
    trending_topics: List[str], *, results_per_page: int = 10, model: str = "gpt-4o-mini"
) -> Crew:
    """Create a Crew that generates TikTok hashtags and scrapes results.

    Inputs:
      - trending_topics: list of trending topics related to the customer's business
    Config:
      - results_per_page: how many results per page to fetch from Apify per scrape
      - model: OpenAI chat model name (requires OPENAI_API_KEY)
    Output:
      - Crew whose kickoff() should return a JSON string with aggregated hashtag results
    """

    if not os.getenv("OPENAI_API_KEY"):
        # Don't hard fail here; allow environments with compatible LLM routing
        pass

    # Tool to scrape TikTok by hashtags
    scrape_tool = TikTokHashtagScrapeTool()

    # Deterministic LLM for generation and summarization
    llm = ChatOpenAI(model=model, temperature=0)

    topics_text = ", ".join(trending_topics)

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

    hashtag_task = Task(
        description=(
            "From these trending topics: '" + topics_text + "'\n"
            "Generate 5-10 TikTok-ready hashtags that are highly relevant.\n"
            "Rules:\n"
            "- No spaces; only letters/numbers.\n"
            "- Do not include the leading '#'.\n"
            "- Avoid duplicates and overly generic tags.\n"
            "Return STRICT JSON: {\"hashtags\": [\"tag1\", \"tag2\", ...]}"
        ),
        agent=researcher,
        expected_output=(
            "A compact JSON object with a single key 'hashtags' containing 5-10 items."
        ),
    )

    scrape_task = Task(
        description=(
            "Using the hashtags from the previous task, call the 'tiktok_hashtag_scrape' tool"
            f" with results_per_page={results_per_page}.\n"
            "For each hashtag, extract: (1) video metadata (hashtags, views, likes),"
            " (2) top creator account details, and (3) a concise summary of the video content.\n"
            "Aggregate everything into STRICT JSON with the following high-level shape:\n"
            "{\n"
            "  \"results\": {\n"
            "    \"<hashtag>\": {\n"
            "      \"videos\": [\n"
            "        {\n"
            "          \"id\": string,\n"
            "          \"url\": string,\n"
            "          \"hashtags\": [string],\n"
            "          \"views\": number,\n"
            "          \"likes\": number,\n"
            "          \"creator\": {\n"
            "             \"username\": string,\n"
            "             \"nickname\": string|null,\n"
            "             \"followers\": number|null\n"
            "          },\n"
            "          \"summary\": string\n"
            "        }\n"
            "      ]\n"
            "    }\n"
            "  }\n"
            "}\n"
            "Notes:\n"
            "- If the tool returns many items, include at least the top 5 by likes.\n"
            "- Infer creator and counts from the tool output fields when present. If missing, use null.\n"
            "- The 'summary' must be 1-2 sentences distilled from title/description/captions.\n"
            "- Only output the JSON."
        ),
        agent=researcher,
        context=[hashtag_task],
        expected_output=(
            "Strict JSON with a 'results' object keyed by hashtag, each containing a 'videos' array."
        ),
    )

    return Crew(agents=[researcher], tasks=[hashtag_task, scrape_task])


def run_search_query_agent(
    trending_topics: List[str], *, results_per_page: int = 10, model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """Convenience runner that returns parsed JSON results.

    Returns a dict with structure:
      {
        "hashtags": ["..."],  # From the first task when parsable
        "results": { ... }     # From the scrape task
      }
    """

    crew = create_search_query_crew(
        trending_topics, results_per_page=results_per_page, model=model
    )
    raw = crew.kickoff()

    # Crew usually returns a string; attempt to parse.
    def _safe_json_loads(s: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(s)
        except Exception:
            return None

    parsed = None
    if isinstance(raw, str):
        parsed = _safe_json_loads(raw)
    elif isinstance(raw, dict):
        parsed = raw

    # If the final output didn't include hashtags, try to parse from first task result
    if not parsed or "results" not in parsed:
        # Try to fetch intermediate artifacts if available
        try:
            artifacts = crew.artifacts  # type: ignore[attr-defined]
        except Exception:
            artifacts = None

        output: Dict[str, Any] = {}
        if parsed:
            output.update(parsed)
        if artifacts and isinstance(artifacts, dict):
            for v in artifacts.values():
                if isinstance(v, str):
                    maybe = _safe_json_loads(v)
                    if maybe and "hashtags" in maybe and "hashtags" not in output:
                        output["hashtags"] = maybe["hashtags"]
        return output or {"error": "Could not parse crew output"}

    return parsed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the search query agent: generate hashtags from topics and scrape TikTok."
    )
    parser.add_argument(
        "--topics",
        required=True,
        help="Comma-separated list of trending topics",
    )
    parser.add_argument(
        "--results-per-page",
        type=int,
        default=10,
        help="Results per page per hashtag scrape (1-50)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI chat model to use",
    )

    args = parser.parse_args()
    topics = [t.strip() for t in args.topics.split(",") if t.strip()]
    data = run_search_query_agent(
        topics, results_per_page=args.results_per_page, model=args.model
    )
    print(json.dumps(data, ensure_ascii=False, indent=2))
