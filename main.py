import os
from typing import TypedDict, List, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from tavily import TavilyClient
from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph


#1. LOAD ENVIRONMENT VARIABLES (NO HARDCODING)

load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
CHAT_DEPLOYMENT = os.getenv("AZURE_CHAT_MODEL_DEPLOYMENT")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not all([AZURE_ENDPOINT, AZURE_API_KEY, CHAT_DEPLOYMENT, TAVILY_API_KEY]):
    raise EnvironmentError("Missing required environment variables")

# 2. INITIALIZE CLIENTS

llm = AzureChatOpenAI(
    api_key=AZURE_API_KEY,
    azure_endpoint=AZURE_ENDPOINT,
    deployment_name=CHAT_DEPLOYMENT,
    temperature=0.3
)

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# 3. SHARED STATE (AGENT MEMORY)

class ResearchState(TypedDict):
    topic: str
    sources: List[dict]
    notes: str
    feedback: Optional[str]
    report: Optional[str]
    accepted: bool

# 4. QUALITY CHECK LOGIC (WRITER DECIDES)

LOW_QUALITY_DOMAINS = {"medium.com", "quora.com", "blogspot.com"}

def evaluate_sources(sources: List[dict]):
    if len(sources) < 3:
        return False, "Too few sources. Find at least 3."

    domains = {urlparse(src["url"]).netloc for src in sources}

    if len(domains) == 1:
        return False, "All sources come from one domain."

    if any(domain in LOW_QUALITY_DOMAINS for domain in domains):
        return False, "Low-quality domains detected."

    return True, None

# 5. RESEARCHER AGENT

def researcher_agent(state: ResearchState):
    print("\n[Researcher] Searching for information...")

    query = state["topic"]

    if state.get("feedback"):
        query += f". Improve research based on feedback: {state['feedback']}"

    search_results = tavily_client.search(
        query=query,
        max_results=5
    )

    sources = []
    for result in search_results["results"]:
        sources.append({
            "title": result["title"],
            "url": result["url"],
            "content": result.get("content", "")
        })

    summary_prompt = f"""
    Summarize the following research into clear bullet-point notes.
    Include facts and figures where possible.

    SOURCES:
    {sources}
    """

    notes = llm.invoke(summary_prompt).content

    return {
        "sources": sources,
        "notes": notes,
        "feedback": None
    }

# 6. WRITER AGENT (CAN ACCEPT OR REJECT)

def writer_agent(state: ResearchState):
    print("[Writer] Evaluating research quality...")

    valid, issue = evaluate_sources(state["sources"])

    if not valid:
        print(f"[Writer] Rejected: {issue}")
        return {
            "accepted": False,
            "feedback": issue
        }

    print("[Writer] Accepted. Writing report...")

    report_prompt = f"""
    Write a professional Markdown research report.

    Topic:
    {state['topic']}

    Research Notes:
    {state['notes']}

    Requirements:
    - Use headings
    - Use bullet points where suitable
    - Include source citations
    """

    report = llm.invoke(report_prompt).content

    return {
        "accepted": True,
        "report": report
    }

# 7. LANGGRAPH WORKFLOW 

def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("researcher", researcher_agent)
    graph.add_node("writer", writer_agent)

    graph.set_entry_point("researcher")

    graph.add_edge("researcher", "writer")

    graph.add_conditional_edges(
        "writer",
        lambda state: "researcher" if not state["accepted"] else "__end__",
        {
            "researcher": "researcher",
            "__end__": "__end__"
        }
    )

    return graph.compile()

def run_research(topic: str) -> str:
    graph = build_graph()

    final_state = graph.invoke({
        "topic": topic,
        "sources": [],
        "notes": "",
        "feedback": None,
        "report": None,
        "accepted": False
    })

    return final_state["report"]

def main():
    topic = input("\nEnter research topic: ")

    graph = build_graph()

    final_state = graph.invoke({
        "topic": topic,
        "sources": [],
        "notes": "",
        "feedback": None,
        "report": None,
        "accepted": False
    })

    print("\n================ FINAL REPORT ================\n")
    print(final_state["report"])

if __name__ == "__main__":
    main()
