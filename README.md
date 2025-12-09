# Revac: Social Deduction Reasoning Agent

🏆 **1st Place - MindGames Arena NeurIPS 2025 (Social Deduction Track, Open Division)**

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)

---

## Overview

Social deduction games such as Mafia present a unique AI challenge: players must reason under uncertainty, interpret incomplete and intentionally misleading information, evaluate human-like communication, and make strategic elimination decisions. Unlike deterministic board games, success depends not on perfect information or brute-force search, but on inference, memory, and adaptability in the presence of deception.

**Revac** is an AI agent designed for multi-agent social deduction games, built on a modular, multi-stage reasoning architecture. The agent evolved from a simple two-stage reasoning system (Revac) to a sophisticated multi-module architecture (Revac_8) that integrates memory-based player profiling, social-graph analysis of accusations and defenses, and dynamic tone selection for adaptive communication.

This repository contains the implementation of the Revac agent family, developed for the MindGames Arena competition, where **Revac_8 achieved first place** in the Social Deduction track. The agent's success highlights the critical role of structured memory and adaptive communication in achieving competitive performance in high-stakes social environments.

> 📖 **For detailed technical documentation, architecture deep-dives, and memory system explanations, see [`src/agents/README.md`](src/agents/README.md)**

---

## Competition Results

Revac_8 secured first place in the **Open Division of the Social Deduction Track** at MindGames Arena NeurIPS 2025.

### Final Standings (TrueSkill Ratings)

| Rank | Agent Name | TrueSkill Rating |
|------|-----------|------------------|
| 🥇 **1st** | **Revac_8** | **13.9** |
| 🥈 2nd | Fractal_SecretMafia_Agent_round2_v25 | 7.8 |
| 🥉 3rd | Fractal_SecretMafia_Agent_round2_v14u | 4.7 |

The competition evaluated agents across multiple games of Secret Mafia, a turn-based social deduction environment with partial observability and asymmetric roles (Village-aligned vs Mafia).

---

## Key Innovations

- **Social Alignment Graph (SAG)**: Structured graph representation of social interactions (accusations, defenses, role claims) enabling collusion detection and group pressure analysis
- **Persistent Memory Module**: Long-term tracking of player profiles and social relationships across all game turns
- **Dynamic Tone Selector (DTS)**: Adaptive communication strategies that adjust tone based on strategic context (aggressive, withdrawing, logically anchoring, contrarian)

---

## Architecture Overview

The Revac agent family evolved through three iterations, each adding new capabilities:

**Revac** → **Revac2** (+ Memory) → **Revac8** (+ Tone Selection)

All agents use a modular pipeline architecture. The final Revac8Agent pipeline:

```
Observation → Memory Update → Reviewer → Tone Selector → Action Agent → Output
```

> 💡 **See [`src/agents/README.md`](src/agents/README.md) for detailed architecture documentation, component explanations, memory system deep-dive.**

---

## Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key or Groq API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/mihiraryaa/mindgames_NeurIPS2025.git
cd mindgames_NeurIPS2025
```

2. **Create and activate virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r src/requirements.txt
```

4. **Configure API keys**

Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here

# Optional: Supabase logging (set ENABLE_LOGGING=True in config.py)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Run Your First Game

```bash
python src/offline_play.py
```

This will run a local Secret Mafia game with multiple Revac agents.

---

## Usage

### Basic Usage

```python
from src.agents import Revac8Agent

# Initialize agent
agent = Revac8Agent("gpt-5-mini", "openai")

# Use in game loop
observation = "Game observation string"
action = agent(observation)
```

### Running Benchmarks

```bash
python -m benchmark.test
```

> 📚 **For more examples including TextArena integration, different model providers, and custom agent creation, see [`src/agents/README.md`](src/agents/README.md)**

---

## Project Structure

```
mindgames_NeurIPS2025/
├── src/
│   ├── agents/              # Agent implementations (Revac, Revac2, Revac8)
│   │   ├── base.py          # Abstract Agent class
│   │   ├── revac.py         # Two-stage reasoning agent
│   │   ├── revac2_1.py      # Memory-enhanced agent
│   │   ├── revac8.py        # Tone-adaptive agent
│   │   ├── judge_agent.py   # Benchmark evaluation agent
│   │   ├── schemas.py       # Pydantic models (Memory, SocialRelation, etc.)
│   │   └── README.md        # Detailed agent documentation
│   │
│   ├── prompts/             # System prompts for each agent variant
│   │   ├── revac_prompts.py
│   │   ├── revac2_1_prompts.py
│   │   └── revac8_prompts.py
│   │
│   ├── config.py            # Environment configuration and API keys
│   ├── utils.py             # Helper functions (get_model, logging)
│   ├── offline_play.py      # Main script for local game simulation
│   └── requirements.txt     # Python dependencies
│
├── envs/                    # Custom TextArena environment configurations
│   ├── SecretMafia/         # Social deduction game environment
│   └── README.md            # Environment documentation
│
├── benchmark/               # Benchmark test suite
│   ├── test.py              # Benchmark runner
│   ├── cases/               # Test cases (challenging scenarios)
│   
│
├── LICENSE                  # MIT License
└── README.md                # This file
```

---

## Agent Variants

This project includes four agent implementations:

- **RevacAgent** - Baseline two-stage reasoning architecture (Reviewer → Action)
- **Revac2Agent** - Adds persistent memory with Player Profiles and Social Alignment Graph
- **Revac8Agent** - Extends Revac2 with dynamic tone selection for adaptive communication
- **HumanAgent** - Manual control interface for testing and debugging

> 📋 **For detailed comparison table, architecture diagrams, memory system explanations, and usage examples, see [`src/agents/README.md`](src/agents/README.md)**

---

## Game Environment: Secret Mafia

The agents are evaluated in a turn-based social deduction game based on Mafia:

- **Roles**: Village-aligned (Villagers, Doctor, Detective) vs Mafia
- **Phases**:
  - **Night**: Private actions (Mafia kills, Doctor protects, Detective investigates)
  - **Day**: Open discussion, voting, and elimination
- **Objective**:
  - **Village**: Eliminate all Mafia members
  - **Mafia**: Achieve numerical parity with Village
- **Challenge**: Partial observability, asymmetric information, intentional deception

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

Built for the **MindGames Arena NeurIPS 2025** challenge. Special thanks to the oraganizing team for providing the game environments and competition infrastructure.
