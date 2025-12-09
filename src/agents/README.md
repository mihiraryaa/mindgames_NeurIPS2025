# Agents

This directory contains AI agent implementations for multi-agent social deduction games, particularly Secret Mafia. All agents are built on a modular, multi-stage reasoning architecture designed for strategic gameplay under partial observability and deception.

All agents inherit from the abstract `Agent` base class and implement a unified interface: `__call__(observation: str) -> str`. This allows different agent variants to be easily swapped and compared in game environments.

The flagship agent, Revac8, achieved strong performance in the MindGames NeurIPS 2025 (Social Deduction Track) through its integration of persistent memory and dynamic communication strategies.

## Agent Comparison

| Agent | Architecture Pipeline | Memory System | Key Innovation |
|-------|---------------------|---------------|----------------|
| **Revac** | Observation → Reviewer → Action | No | Baseline two-stage reasoning: separate analysis from action generation |
| **Revac2.1** | Observation → Memory Update → Reviewer → Action | Yes | Persistent memory with Player Profiles and Social Alignment Graph |
| **Revac8** | Observation → Memory Update → Reviewer → Tone Selector → Action | Yes | Dynamic tone selection for adaptive communication strategies |
| **HumanAgent** | Observation → Human Input | No | Manual control for testing and debugging |

## Agent Architectures

### Base Classes

#### Agent (Abstract Base Class)
`src/agents/base.py`

All agents inherit from this abstract class and must implement:
```python
def __call__(self, observation: str) -> str:
    """Process observation and return action"""
    pass
```

#### HumanAgent
Allows manual human input for testing, debugging, and playing alongside AI agents.

```python
from src.agents import HumanAgent

agent = HumanAgent()
action = agent(observation)  # Prompts for keyboard input
```

---

### RevacAgent - Two-Stage Reasoning

**Architecture Flow:**
```
Observation → Reviewer Agent → Action Agent → Output
```

The foundational architecture that separates strategic analysis from action generation:

1. **Reviewer Agent**: Analyzes the observation, performs logical deductions, detects contradictions, and assesses player roles
2. **Action Agent**: Takes the observation + review to formulate the final natural-language action

This separation ensures outputs are grounded in structured analysis, minimizing hallucinations and inconsistent actions.

**When to use:** Baseline agent for simple games or when memory overhead is a concern.

**Example:**
```python
from src.agents import RevacAgent

agent = RevacAgent("gpt-5-mini", "openai")
action = agent(observation)
```

---

### Revac2Agent - Memory-Enhanced

**Architecture Flow:**
```
Observation → Memory Update → Reviewer (with memory) → Action Agent → Output
```

Extends RevacAgent with a persistent memory module that overcomes short-term memory limitations of standard LLM agents.

**Memory Components:**

- **Player Profiles**: Textual summaries of each player's behavioral history, including their claims, voting patterns, past actions, and perceived consistency/credibility

- **Social Alignment Graph (SAG)**: A structured representation of social relationships that tracks:
  - **Accusations**: Player A accuses Player B of being Mafia
  - **Defenses/Support**: Player A defends or supports Player B
  - **Role Claims**: Player A claims to be Detective, Doctor, etc.

The SAG enables advanced reasoning capabilities:
- **Collusion Detection**: Identifies mutual defense patterns suggesting hidden alliances
- **Group Pressure Analysis**: Detects coordinated accusations or potential mislynches
- **Contradiction Grounding**: Provides non-textual anchors for long-term reasoning

**When to use:** Games requiring long-term tracking of player behavior and social dynamics (e.g., Secret Mafia).

**Example:**
```python
from src.agents import Revac2Agent

agent = Revac2Agent("gpt-5-mini", "openai")
action = agent(observation)  # Memory persists across calls
```

---

### Revac8Agent - Tone-Adaptive

**Architecture Flow:**
```
Observation → Memory Update → Reviewer → Tone Selector → Action Agent (with tone) → Output
```

Extends Revac2Agent with a Dynamic Tone Selector (DTS) that adapts communication style based on strategic context.

**Key Features:**

All memory capabilities of Revac2Agent, plus:

**Dynamic Tone Selection**: A third-stage module that selects optimal communication tone/style based on the reviewer's analysis and current game state.

**Supported Tones:**
- **Aggressive/Pressuring**: Forces suspects to respond or make mistakes
- **Withdrawing/Passive**: Deflects suspicion, observes without becoming a target
- **Logically Anchoring**: Establishes consensus using firm, rational arguments
- **Contrarian/Skeptical**: Breaks false consensus, tests claim validity

The DTS ensures the agent's output is not only logically sound but also socially and rhetorically effective, transforming it from a deduction machine into a persuasive social actor.

**When to use:** Competitive gameplay requiring sophisticated communication strategies and social camouflage.

**Example:**
```python
from src.agents import Revac8Agent

agent = Revac8Agent("gpt-5-mini", "openai")
action = agent(observation)  # Memory + dynamic tone selection
```

---

### BenchmarkJudgeAgent

A specialized LLM-based evaluation agent that scores the reasoning quality of other agents on a 0-5 scale. It assesses logical soundness, evidence usage, contradiction detection, and hallucination avoidance.

**Note:** This agent is used for benchmarking and evaluation only, not for actual gameplay.

```python
from src.agents.judge_agent import BenchmarkJudgeAgent

judge = BenchmarkJudgeAgent("gpt-5-nano")
result = judge.evaluate(transcript, agent_reasoning, ground_truth)
# Returns: JudgeResponse(score=4.5, explanation="...")
```

---

## Memory System Deep Dive

The memory system (used in Revac2Agent and Revac8Agent) is the core innovation enabling long-term strategic reasoning.

### Memory Structure

Memory is represented by the `RevacMemory` schema defined in `schemas.py`:

```python
class RevacMemory:
    player_profiles: str              # Textual behavioral summaries
    social_alignment_graph: List[SocialRelation]  # Structured social interactions
```

### Player Profiles

String-based summaries tracking:
- Role claims (e.g., "Player 2 claimed Detective on Day 1")
- Voting history (e.g., "Voted for Player 3 on Day 1, switched to Player 5")
- Behavioral patterns (e.g., "Often defensive when questioned")
- Credibility indicators (e.g., "Claim contradicts game log")
- Observed contradictions

### Social Alignment Graph (SAG)

The SAG transforms raw dialogue into a machine-readable relational structure, enabling graph-based reasoning.

**Structure:**
Each `SocialRelation` represents a directed social interaction:
```python
class SocialRelation:
    player: str    # e.g., "Player 0"
    relation: str  # "accuses", "defends", or "claims_role"
    target: str    # e.g., "Player 1" or "Detective"
```

**Example SAG:**
```json
[
  {"player": "Player 0", "relation": "accuses", "target": "Player 1"},
  {"player": "Player 2", "relation": "defends", "target": "Player 1"},
  {"player": "Player 0", "relation": "claims_role", "target": "Detective"},
  {"player": "Player 1", "relation": "claims_role", "target": "Detective"}
]
```

**What the SAG Enables:**

1. **Collusion Detection**: Strong mutual defense patterns (A defends B, B defends A) over multiple rounds suggest hidden alliances like Mafia partnerships

2. **Group Pressure Analysis**: High accusation frequency against one player reveals group consensus or potential coordinated attacks

3. **Contradiction Detection**: Multiple players claiming the same role (e.g., two Detectives) become structurally evident

4. **Strategic Voting Patterns**: Tracking who votes for whom reveals alliances, bandwagoning, and opportunistic behavior

The memory updates every turn via a dedicated GPT-4o call with JSON mode, ensuring the memory remains consistent and well-structured.

---

## Quick Start

### Basic Usage

```python
from src.agents import RevacAgent, Revac2Agent, Revac8Agent

# Choose an agent variant
agent = Revac2Agent("gpt-5-mini", "openai")

# Use in a game loop
observation = "Game observation string from environment"
action = agent(observation)
print(action)
```

### Integration with TextArena

```python
import textarena as ta
from src.agents import Revac2Agent

# Initialize agents
agents = {
    0: Revac2Agent("gpt-5-mini", "openai"),
    1: Revac2Agent("gpt-5-mini", "openai"),
    # ... more agents
}

# Run game
env = ta.make(env_id="SecretMafia-v0")
env.reset(num_players=6)

done = False
while not done:
    player_id, observation = env.get_observation()
    action = agents[player_id](observation)
    done, step_info = env.step(action=action)

rewards, game_info = env.close()
```

### Model Providers

Agents support multiple LLM providers:

**OpenAI:**
```python
agent = Revac8Agent("gpt-5-mini", "openai")  # Requires OPENAI_API_KEY
```

**Groq:**
```python
agent = Revac8Agent("llama-3.1-70b-versatile", "groq")  # Requires GROQ_API_KEY
```

Configure API keys in `.env` or environment variables (see `src/config.py`).

---

## Creating Custom Agents

To create a new agent variant:

### 1. Inherit from Agent Base Class

```python
from src.agents.base import Agent

class MyCustomAgent(Agent):
    def __init__(self, model_name: str, model_provider: str):
        super().__init__()
        self.model_name = model_name
        self.model_provider = model_provider
        # Initialize your model, memory, etc.

    def __call__(self, observation: str) -> str:
        # Your agent logic here
        return "My action"
```

### 2. Implement Required Methods

**Required:**
- `__call__(self, observation: str) -> str`: Main agent logic

**Optional:**
- `evaluate(self, observation: str) -> EvaluationResponse`: For benchmark evaluation

### 3. Add Prompts

Create a new prompt file in `src/prompts/`:
```python
# src/prompts/my_agent_prompts.py

my_system_prompt = """
Your agent's system prompt here...
"""

my_action_prompt = """
Your action generation prompt here...
"""
```

### 4. Register Agent (Optional)

Add to `src/agents/__init__.py`:
```python
from .my_agent import MyCustomAgent
```

---

## Files in This Directory

| File | Description |
|------|-------------|
| `base.py` | Abstract `Agent` base class and `HumanAgent` implementation |
| `revac.py` | `RevacAgent` - Two-stage reasoning (Reviewer → Action) |
| `revac2_1.py` | `Revac2Agent` - Memory-enhanced with Player Profiles and SAG |
| `revac8.py` | `Revac8Agent` - Tone-adaptive with Dynamic Tone Selector |
| `judge_agent.py` | `BenchmarkJudgeAgent` - LLM-based reasoning quality evaluator |
| `schemas.py` | Pydantic models: `EvaluationResponse`, `RevacMemory`, `SocialRelation` |
| `__init__.py` | Package exports |

---
