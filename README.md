# Mind Games NeurIPS 2025


## Setup

1. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. **Install dependencies**
```bash
pip install -r src/requirements.txt
```

3. **Configure API keys**

Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here
```

## Running Agents

### Play a game locally
```bash
python -m src.offline_play
```

### Run benchmark tests
```bash
python -m benchmark.test
```

This will:
- Test all agent variants (Revac, Revac2.1, Revac8)
- Evaluate on benchmark cases
- Save results to `benchmark/results/`

## Project Structure

- `src/agents/` - Agent implementations (revac.py, revac2_1.py, revac8.py)
- `src/prompts/` - System prompts for each agent
- `benchmark/` - Benchmark test suite
- `envs/` - Game environment configurations

## Available Agents

- **RevacAgent** - Two-stage architecture (reviewer → action)
- **Revac2Agent** - Adds persistent memory with player profiles
- **Revac8Agent** - Extended variant with additional features
