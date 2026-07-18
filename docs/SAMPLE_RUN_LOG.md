# Sample Run Log

This is a **reference example** of what the console output looks like during a
normal run. Actual logs are generated on your local machine. Use this to
recognize a healthy run and to spot where things go wrong.

---

## A) CLI run — `python main.py --keywords "AI" "인공지능"`

```text
Starting briefing - keywords: AI, 인공지능

# Agent: News collection specialist
## Task: Collect the latest news for these keywords: [AI, 인공지능]
   Using tool: news_search
   [keyword: AI] 5 results: ...
   [keyword: 인공지능] 5 results: ...
   Using tool: rss_fetch
   [RSS] 8 articles collected: ...
## Output: ArticleList(articles=[... 18 items ...])

# Agent: News curation analyst
## Task: Review the collected article list. Remove duplicates, score, keep top 6.
## Output: RankedArticleList(articles=[... 6 items ...])

# Agent: News briefing writer
## Task: Write today's news briefing from the selected articles.
## Output: BriefingReport(date="2026-06-09", keywords=[...], markdown="...")

==================================================
# News Briefing (2026-06-09)
## AI
### OpenAI releases new agentic model
- English source -> English summary...
- Source: https://...
## 인공지능
### 삼성, 새 AI 칩 공개
- 한글 기사 -> 한글 요약...
- Source: https://...

---
## Search conditions for this briefing
| Item | Value |
| --- | --- |
| Keywords | `AI`, `인공지능` |
| Articles per keyword | 5 |
| Final selection | top 6 |
| Time window | last 7 days |
| Model | anthropic/claude-sonnet-4-6 |
| Generated at | 2026-06-09 08:00 |
==================================================

Briefing complete -> outputs/briefing_2026-06-09.md
  [slack] briefing delivered.
```

---

## B) Streamlit run — `streamlit run app.py`

```text
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.0.10:8501

# Agent: News collection specialist
   Using tool: news_search ...
   Using tool: rss_fetch ...
# Agent: News curation analyst ...
# Agent: News briefing writer ...
  [slack] briefing delivered.
```

To stop the Streamlit server: press `Ctrl + C` in the terminal.

---

## Reading the log — what to look for

| Line | Meaning |
|------|---------|
| `Using tool: news_search` | Collector is calling Tavily |
| `Using tool: rss_fetch` | Collector is calling RSS feeds |
| `[RSS] N articles collected` | RSS adapter worked |
| `## Output: ArticleList(...)` | Pydantic contract enforced OK |
| `[slack] briefing delivered.` | Slack push succeeded |
| `[slack] disabled ...` | SLACK_ENABLED is not true (expected if off) |

## Common error lines

| Log line | Cause | Fix |
|----------|-------|-----|
| `404 not_found_error: model` | wrong/retired model ID | check LLM_MODEL |
| `[warn] search failed ... attempt 1/3` | transient Tavily/network issue | usually self-recovers via retry |
| `[error] RSS parse failed: <url>` | a feed is down/changed | other feeds still proceed |
| `[slack] delivery failed: 403` | bad/expired webhook URL | re-issue the webhook |
| `Missing environment variables: ...` | keys not set | fill in .env |
```
