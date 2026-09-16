import os
import sys
from dotenv import load_dotenv
from agents.assistant import create_assistant

# Load environment variables from .env if present
load_dotenv()

def main():
    print("=" * 60)
    print("🚀 Agno Agent Framework (Gemini Edition) initialized!")
    print("=" * 60)

    # Check for GEMINI_API_KEY or GOOGLE_API_KEY
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not gemini_key:
        print("⚠️  GEMINI_API_KEY not found in environment!")
        print("   Please create a '.env' file based on '.env.example' and set GEMINI_API_KEY.")
        print("   Example:")
        print("     cp .env.example .env")
        print("     echo 'GEMINI_API_KEY=your_key_here' > .env")
        print("\n✅ Add your GEMINI_API_KEY and run 'python main.py' to execute your agent.")
        return

    print("🔑 Gemini API key detected.")
    try:
        agent = create_assistant(enable_web_search=True)
        query = "What are the latest key highlights of the Agno multi-agent framework?"
        print(f"\n🤖 Running Agent with query: '{query}'\n")
        agent.print_response(query, stream=True)
    except Exception as e:
        print(f"\n❌ Error running agent: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()

