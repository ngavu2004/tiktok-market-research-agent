from __future__ import annotations
from typing import Any, Dict, List, Optional

import os
import json
from apify_client import ApifyClient
from dotenv import load_dotenv
load_dotenv()

def tiktok_scrape_tool(hashtags: List[str]):
    # Initialize the ApifyClient with your API token
    client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

    # Prepare the Actor input
    run_input = {
        "hashtags": hashtags,
        "resultsPerPage": 100,
        "profileScrapeSections": ["videos"],
        "profileSorting": "latest",
        "excludePinnedPosts": False,
        "searchSection": "",
        "maxProfilesPerQuery": 10,
        "scrapeRelatedVideos": False,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSubtitles": False,
        "shouldDownloadSlideshowImages": False,
        "shouldDownloadAvatars": False,
        "shouldDownloadMusicCovers": False,
        "proxyCountryCode": "None",
    }

    # Run the Actor and wait for it to finish
    run = client.actor("GdWCkxBtKWOsKjdch").call(run_input=run_input)

    # Fetch and print Actor results from the run's dataset (if there are any)
    res = {"data": []}
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        res["data"].append(item)
    
    # dump res to result.json file
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    return res

if __name__ == "__main__":
    import argparse
    import json
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

    args = parser.parse_args()

    # Allow passing token via flag, otherwise fall back to env var
    if args.apify_token:
        os.environ["APIFY_API_TOKEN"] = args.apify_token

    if not os.getenv("APIFY_API_TOKEN"):
        print("Error: APIFY_API_TOKEN is not set and --apify-token was not provided.", file=sys.stderr)
        sys.exit(1)

    # Normalize and parse hashtags CSV
    hashtags = [h.strip().lstrip("#") for h in args.hashtags.split(",") if h.strip()]
    if not hashtags:
        print("Error: --hashtags must contain at least one value.", file=sys.stderr)
        sys.exit(1)

    try:
        result = tiktok_scrape_tool(hashtags)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error running scraper: {e}", file=sys.stderr)
        sys.exit(1)

