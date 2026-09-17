import os
from agno.agent import Agent
from agno.models.google import Gemini

def get_model(model_id: str | None = None) -> Gemini:
    """
    Returns configured Google Gemini model object.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    selected_model = model_id or os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    return Gemini(id=selected_model, api_key=api_key)

def create_assistant(
    model_id: str | None = None,
    enable_web_search: bool = True,
) -> Agent:
    """
    Factory function to initialize an Agno Agent using Google Gemini.
    """
    tools = []
    if enable_web_search:
        try:
            from agno.tools.duckduckgo import DuckDuckGoTools
            tools.append(DuckDuckGoTools())
        except ImportError:
            pass

    agent = Agent(
        name="Team Assistant",
        model=get_model(model_id),
        tools=tools,
        instructions=[
            "You are an intelligent AI assistant built with the Agno framework powered by Google Gemini.",
            "Always provide helpful, precise, and well-structured responses in Markdown.",
            "When web search tools are available, use them to find up-to-date and accurate context.",
        ],
        markdown=True,
    )
    return agent

