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

Use as a CrewAI Tool:
```
from crewai import Agent, Task, Crew
from src.tools import TikTokHashtagScrapeTool

scrape_tool = TikTokHashtagScrapeTool()

agent = Agent(
  role="TikTok Researcher",
  goal="Analyze trending posts for given hashtags",
  backstory="",
  tools=[scrape_tool],
)

task = Task(
  description="Scrape posts for #cats and #dogs",
  agent=agent,
  expected_output="JSON with posts",
  tools=[scrape_tool],
  args={"hashtags": ["cats", "dogs"], "results_per_page": 10},
)

crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
print(result)
```

Notes:
- Requires `APIFY_API_TOKEN` set in environment or .env.
- The tool accepts either a list of tags or a comma-separated string. Leading `#` is optional.

## Project structure
```
src/
  tools/
    tiktok_scrape_tool.py  # CLI tool: scrapes TikTok by hashtags via Apify
```