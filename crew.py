"""
Crew assembly - the core of the agent system.

Why separate this from main.py?
- crew.py is "the agent system itself"; main.py is "how to run it".
- In Phase 2, when main.py is swapped for app.py (Streamlit), this file is
  imported and reused as-is. The agent logic is never touched.
"""

from crewai import Crew, Process

from agents.collector import build_collector
from agents.ranker import build_ranker
from agents.writer import build_writer
from tasks.tasks import build_collect_task, build_rank_task, build_write_task


def build_crew(keywords: list[str]) -> Crew:
    """Assemble and return a briefing Crew for the given keywords.

    Args:
        keywords: keywords the briefing should cover

    Returns:
        A ready-to-run Crew object (run with .kickoff())
    """
    # 1) Create the three agents
    collector = build_collector()
    ranker = build_ranker()
    writer = build_writer()

    # 2) Define tasks and chain them via context (collect -> rank -> write)
    collect_task = build_collect_task(collector, keywords)
    rank_task = build_rank_task(ranker, collect_task)
    write_task = build_write_task(writer, rank_task, keywords)

    # 3) Bundle into a Crew - sequential = top-to-bottom execution
    return Crew(
        agents=[collector, ranker, writer],
        tasks=[collect_task, rank_task, write_task],
        process=Process.sequential,
        verbose=True,  # observability: log the full run
    )
