"""
Example 1: Simple Agno Agent using Google Gemini
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure root repository directory is in Python path
sys.path.append(str(Path(__file__).parent.parent))

from agno.agent import Agent
from agents import get_model

load_dotenv()

agent = Agent(
    name="General Assistant",
    model=get_model("gemini-2.5-flash"),
    instructions=[
        "Gia vang hom nay",
        "Format your responses in clean Markdown.",
    ],
    markdown=True,
)

if __name__ == "__main__":
    print("🤖 Querying Agno Simple Agent...\n")
    agent.print_response("Explain how multi-agent systems work in 3 short bullet points.", stream=True)
