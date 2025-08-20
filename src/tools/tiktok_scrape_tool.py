from __future__ import annotations
from typing import Any, Dict, List, Optional

import os
import json
from apify_client import ApifyClient
from crewai_tools import BaseTool
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

load_dotenv()


class TikTokHashtagScrapeInput(BaseModel):
    """Input schema for TikTok hashtag scraping."""

    hashtags: List[str] = Field(
        ..., description="List of hashtags to scrape (without the leading #)."
    )
    results_per_page: int = Field(
        10, ge=1, le=50, description="How many results per page to fetch from Apify."
    )

    @validator("hashtags", pre=True)
    def normalize_hashtags(cls, v):  # type: ignore[no-untyped-def]
        # Accept a comma-separated string or a list; strip leading '#'
        if isinstance(v, str):
            v = [h.strip() for h in v.split(",") if h.strip()]
        if isinstance(v, list):
            return [str(h).strip().lstrip("#") for h in v if str(h).strip()]
        raise ValueError("hashtags must be a list or comma-separated string")


def tiktok_scrape_tool(
    hashtags: List[str], *, results_per_page: int = 10, write_to_file: bool = False
) -> Dict[str, Any]:
    """Scrape TikTok by hashtags via Apify and return the aggregated results.

    Parameters:
        hashtags: list of hashtags (without '#').
        results_per_page: number of results per page.
        write_to_file: if True, writes the JSON result to result.json.

    Returns:
        Dict with a single key "data" containing the list of scraped items.
    """

    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        raise RuntimeError(
            "APIFY_API_TOKEN is not set. Please set it in your environment or .env file."
        )

    # Initialize the ApifyClient with your API token
    client = ApifyClient(token)

    # Prepare the Actor input
    run_input = {
        "hashtags": hashtags,
        "resultsPerPage": results_per_page,
        "profileScrapeSections": ["videos"],
        "profileSorting": "latest",
        "excludePinnedPosts": False,
        "searchSection": "",
        "maxProfilesPerQuery": 10,
        "scrapeRelatedVideos": False,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSubtitles": True,
        "shouldDownloadSlideshowImages": False,
        "shouldDownloadAvatars": False,
        "shouldDownloadMusicCovers": False,
        "proxyCountryCode": "None",
    }

    # Run the Actor and wait for it to finish
    run = client.actor("GdWCkxBtKWOsKjdch").call(run_input=run_input)

    # Fetch Actor results from the run's dataset (if there are any)
    res: Dict[str, Any] = {"data": []}
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        res["data"].append(item)

    if write_to_file:
        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)

    return res


class TikTokHashtagScrapeTool(BaseTool):
    """CrewAI Tool that scrapes TikTok for a list of hashtags using Apify."""

    name: str = "tiktok_hashtag_scrape"
    description: str = (
        "Scrape TikTok posts for the given list of hashtags and return the JSON results. "
        "Requires APIFY_API_TOKEN to be set."
    )
    args_schema: type[BaseModel] = TikTokHashtagScrapeInput

    def _run(
        self, hashtags: List[str], results_per_page: int = 10, **_: Any
    ) -> Dict[str, Any]:
        return tiktok_scrape_tool(
            hashtags=hashtags, results_per_page=results_per_page, write_to_file=False
        )


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Scrape TikTok data by hashtags using Apify."
    )
    parser.add_argument(
        "--hashtags",
        required=True,
        help="Comma-separated list of hashtags (with or without #), e.g. 'cats,dogs'",
    )
    parser.add_argument(
        "--apify-token",
        dest="apify_token",
        help="Apify API token. If omitted, reads from APIFY_API_TOKEN env var.",
    )
    parser.add_argument(
        "--results-per-page",
        type=int,
        default=10,
        help="Number of results per page (1-50)",
    )

    args = parser.parse_args()

    # Allow passing token via flag, otherwise fall back to env var
    if args.apify_token:
        os.environ["APIFY_API_TOKEN"] = args.apify_token

    if not os.getenv("APIFY_API_TOKEN"):
        print(
            "Error: APIFY_API_TOKEN is not set and --apify-token was not provided.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Normalize and parse hashtags CSV
    hashtags = [h.strip().lstrip("#") for h in args.hashtags.split(",") if h.strip()]
    if not hashtags:
        print("Error: --hashtags must contain at least one value.", file=sys.stderr)
        sys.exit(1)

    try:
        result = tiktok_scrape_tool(
            hashtags, results_per_page=args.results_per_page, write_to_file=True
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error running scraper: {e}", file=sys.stderr)
        sys.exit(1)

