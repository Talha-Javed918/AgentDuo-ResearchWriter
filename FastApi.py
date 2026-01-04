from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from main import run_research

app = FastAPI(
    title="Multi-Agent Research API",
    description="Researcher + Writer agent system using LangGraph",
    version="1.0.0"
)

class ResearchRequest(BaseModel):
    topic: str

class ResearchResponse(BaseModel):
    report: str

@app.post("/research", response_model=ResearchResponse)
def research_endpoint(request: ResearchRequest):
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    report = run_research(request.topic)

    return {"report": report}

@app.get("/")
def health_check():
    return {"status": "running"}
