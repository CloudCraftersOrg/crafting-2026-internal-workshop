"""API backend for HORROCRUXES demo UI.

Simple FastAPI server that proxies requests to the deployed AgentCore runtime.
"""

import os
import sys
import json
import uuid
from pathlib import Path

# Add parent app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from workshop_agent.config import load_config

app = FastAPI(title="HORROCRUXES Demo API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config
config = load_config()

# Get agent runtime ARN from environment
AGENT_RUNTIME_ARN = os.environ.get("AGENT_RUNTIME_ARN", "")
if not AGENT_RUNTIME_ARN:
    print("❌ ERROR: AGENT_RUNTIME_ARN environment variable not set", file=sys.stderr)
    sys.exit(1)


class QueryRequest(BaseModel):
    prompt: str


class QueryResponse(BaseModel):
    answer: str
    session_id: str


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "HORROCRUXES by Team Slytherin"}


@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """Send a query to the deployed AgentCore runtime."""

    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    try:
        # Create Bedrock AgentCore client
        client = boto3.client(
            "bedrock-agentcore",
            region_name=config.aws_region,
        )

        # Generate session ID
        session_id = str(uuid.uuid4())

        # Prepare request body
        body = json.dumps({
            "inputText": request.prompt.strip(),
            "sessionId": session_id
        })

        # Invoke the runtime
        response = client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            runtimeSessionId=session_id,
            payload=body.encode("utf-8"),
            contentType="application/json",
            accept="application/json",
        )

        # Extract response from streaming body
        raw_body = response.get("response") or response.get("body")
        if raw_body is None:
            raise Exception("No response body from agent")

        raw_bytes = raw_body.read() if hasattr(raw_body, "read") else raw_body
        raw_str = raw_bytes.decode("utf-8", errors="replace")

        # Parse JSON response
        data = json.loads(raw_str)
        output_text = (
            data.get("outputText") or
            data.get("response") or
            data.get("message") or
            str(data)
        )

        return QueryResponse(
            answer=output_text,
            session_id=session_id,
        )

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"AgentCore error ({error_code}): {error_msg}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    print("🐍 Starting HORROCRUXES Demo API on http://localhost:8000")
    print(f"🔗 Agent Runtime: {AGENT_RUNTIME_ARN}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
