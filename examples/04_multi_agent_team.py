"""
Example 4: Agno Multi-Agent Team using Google Gemini
Demonstrates delegating tasks between specialized agents (Researcher & Writer).
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))

from agno.agent import Agent
from agno.team import Team
from agents import get_model

load_dotenv()

# 1. Define specialized member agents
researcher = Agent(
    name="Researcher",
    role="Research technical concepts and gather factual details",
    model=get_model("gemini-2.5-flash"),
)

writer = Agent(
    name="Writer",
    role="Synthesize technical research into clean, executive markdown summaries",
    model=get_model("gemini-2.5-flash"),
)

# 2. Define the team leader that coordinates members
team = Team(
    name="Technical Editorial Team",
    members=[researcher, writer],
    model=get_model("gemini-2.5-flash"),
    instructions=[
        "First delegate research to the Researcher agent.",
        "Then pass the research findings to the Writer agent to produce a polished summary.",
    ],
    markdown=True,
)

if __name__ == "__main__":
    print("👥 Querying Agno Multi-Agent Team...\n")
    team.print_response("Explain how agentic workflows differ from standard LLM prompts in 2 key points.", stream=True)
