import json
from typing import Dict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import OPENAI_API_KEY


class JudgeResponse(BaseModel):
    """Structured response from the benchmark judge."""
    score: float = Field(
        ...,
        ge=0,
        le=5,
        description="Reasoning quality score from 0 to 5"
    )
    explanation: str = Field(
        ...,
        description="Concise justification for the score"
    )


JUDGE_SYSTEM_PROMPT = """You are evaluating the reasoning ability of an AI agent playing a Mafia deduction game.

You will receive:
1. The game transcript (Observation State)
2. The agent's reasoning
3. The ground truth roles

Your task:
- Evaluate whether the agent's reasoning steps were logically justified.
- Check if it used real information from the transcript.
- Check if it avoided hallucination.
- Check whether it correctly interpreted behaviors, contradictions, claims.
- You are **not** scoring role correctness — only reasoning quality.

Assign a reasoning quality score from 0 to 5.

You must respond with a JSON object containing:
- "score": A number from 0 to 5 representing reasoning quality
- "explanation": A concise justification for the score
"""


class BenchmarkJudgeAgent:
    """
    LLM-based judge agent for evaluating reasoning quality in the benchmark.
    Uses structured output via JSON mode.
    """
    
    def __init__(self, model_name: str = "gpt-5-nano"):
        self.model_name = model_name
        self.model = ChatOpenAI(
            model=model_name,
            api_key=OPENAI_API_KEY,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
    
    def evaluate(self, transcript: str, agent_reasoning: str, ground_truth: Dict) -> JudgeResponse:
        """
        Evaluate the reasoning quality of an agent's response.
        
        Args:
            transcript: The game observation state/transcript
            agent_reasoning: The agent's reasoning explanation
            ground_truth: Dictionary containing ground truth roles
            
        Returns:
            JudgeResponse with score (0-5) and explanation
        """
        user_content = f"""---
Game Transcript:
{transcript}

Agent's Reasoning:
{agent_reasoning}

Ground Truth:
{json.dumps(ground_truth, indent=2)}
"""
        
        sys = SystemMessage(content=JUDGE_SYSTEM_PROMPT)
        user = HumanMessage(content=user_content)
        prompt = [sys, user]
        
        try:
            response = self.model.invoke(prompt)
            json_data = json.loads(response.content)
            result = JudgeResponse(**json_data)
            return result
        except Exception as e:
            print(f"Error in judge evaluation: {e}")
            return JudgeResponse(score=0.0, explanation=f"Error: {e}")
