# Tiktok market research agent
Understand the content that trends for customer niche and create a tiktok draft suggestion for future posts


## Install
```
python -m venv .venv
source .venv/Scripts/activate  # on Windows bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Configure the API token
Option A: .env file (auto-loaded)
```
# In the project root
echo "APIFY_API_TOKEN=YOUR_APIFY_TOKEN_HERE" > .env
```

Option B: pass via flag
- Use the `--apify-token` CLI option shown below.

## Usage
Run as a module (recommended):
```
python -m src.tools.tiktok_scrape_tool --hashtags cats,dogs
```

## Project structure
```
src/
  tools/
    tiktok_scrape_tool.py  # CLI tool: scrapes TikTok by hashtags via Apify
```