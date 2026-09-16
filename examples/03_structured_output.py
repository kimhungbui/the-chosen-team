"""
Example 3: Agno Agent with Structured Pydantic Output using Google Gemini
"""
import sys
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))

from agno.agent import Agent
from agents import get_model

load_dotenv()

class MovieReview(BaseModel):
    title: str = Field(description="Title of the movie")
    genre: str = Field(description="Primary genre of the movie")
    rating: float = Field(description="Rating out of 10.0")
    key_takeaways: List[str] = Field(description="List of 3 main highlights or themes")

agent = Agent(
    name="Movie Critic",
    model=get_model("gemini-2.5-flash"),
    output_schema=MovieReview,
    instructions=["Generate a structured movie review for the requested movie."],
)

if __name__ == "__main__":
    print("🎬 Querying Agno Agent for Structured Output...\n")
    response = agent.run("Review the sci-fi movie 'Interstellar'.")
    review: MovieReview = response.content
    print(f"Movie Title: {review.title}")
    print(f"Genre: {review.genre}")
    print(f"Rating: {review.rating}/10")
    print("Key Takeaways:")
    for takeaway in review.key_takeaways:
        print(f" - {takeaway}")
