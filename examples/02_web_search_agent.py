"""
Example 2: Agno Web Search Agent using Google Gemini & DuckDuckGo Tools
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))

from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agents import get_model

load_dotenv()

agent = Agent(
    name="Web Researcher",
    model=get_model("gemini-2.5-flash"),
    tools=[DuckDuckGoTools()],
    instructions=[
        "Use web search tools to retrieve accurate factual data when requested.",
        "Include source references or key takeaways in clean Markdown.",
    ],
    markdown=True,
)

if __name__ == "__main__":
    print("🔍 Querying Agno Web Search Agent...\n")
    agent.print_response("Search for the latest news on NASA Space Exploration missions in 2026.", stream=True)
