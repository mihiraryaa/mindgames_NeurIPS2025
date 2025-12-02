import json
import os
import sys
import time
from typing import Dict, Any, List
from rich.console import Console, Group
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agents.revac import RevacAgent
from src.agents.revac2_1 import Revac2Agent
from src.agents.revac8 import Revac8Agent
from src.agents.judge_agent import BenchmarkJudgeAgent

console = Console()

SHOW_DETAILED_OUTPUT = True


def load_benchmark_data(filepath: str) -> Dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_metric_a(predicted_roles: Dict[str, str], ground_truth_roles: Dict[str, str]) -> float:
    """
    Calculates Metric A: Role Identification Accuracy.
    Score = (# correct roles) / (total players)
    """
    if not predicted_roles:
        return 0.0

    correct_count = 0
    total_players = len(ground_truth_roles)

    for player, true_role in ground_truth_roles.items():
        pred_role = predicted_roles.get(player)
        if pred_role and pred_role.lower().strip() == true_role.lower().strip():
            correct_count += 1

    return correct_count / total_players if total_players > 0 else 0.0


judge_agent = BenchmarkJudgeAgent(model_name="gpt-5-mini")


def evaluate_reasoning_with_llm(transcript: str, agent_reasoning: str, ground_truth: Dict) -> Dict:
    """
    Evaluates reasoning using the BenchmarkJudgeAgent (Metric B).
    """
    judge_result = judge_agent.evaluate(transcript, agent_reasoning, ground_truth)
    return {"score": judge_result.score, "explanation": judge_result.explanation}


def run_benchmark():
    benchmark_file = os.path.join(os.path.dirname(__file__), 'mafia_benchmark.json')
    data = load_benchmark_data(benchmark_file)
    test_cases = data['test_cases']

    agents_to_test = [
        ("Revac", RevacAgent(model_name="gpt-5-mini", model_provider="openai")),
        ("Revac2.1", Revac2Agent(model_name="gpt-5-mini", model_provider="openai")),
        ("Revac8", Revac8Agent(model_name="gpt-5-mini", model_provider="openai")),
    ]

    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(results_dir, exist_ok=True)

    all_agent_results = []

    console.print(Panel.fit("[bold blue]Mafia Agent Benchmark[/bold blue]", subtitle="Evaluating Deduction & Reasoning"))

    for agent_name, agent in agents_to_test:
        console.print(f"\n[bold yellow]Testing Agent: {agent_name}[/bold yellow]")

        agent_results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[cyan]Running {len(test_cases)} test cases...", total=len(test_cases))

            for test_case in test_cases:
                case_id = test_case['id']
                scenario = test_case['scenario_type']
                observation = test_case['observation_state']
                ground_truth = test_case['ground_truth']

                progress.update(task, description=f"Case {case_id}: {scenario[:30]}...")

                # 1. run agent using evaluate() method
                try:
                    eval_response = agent.evaluate(observation)
                    predicted_roles = eval_response.roles
                    agent_reasoning = eval_response.explanation
                    response_raw = f"Roles: {predicted_roles}\nExplanation: {agent_reasoning}"
                except Exception as e:
                    console.print(f"[red]Error running agent on case {case_id}: {e}[/red]")
                    predicted_roles = {}
                    agent_reasoning = ""
                    response_raw = str(e)

                # 2. calculate metric A
                metric_a_score = calculate_metric_a(predicted_roles, ground_truth['roles'])

                # 3. calculate metric B (LLM Judge)
                metric_b_result = evaluate_reasoning_with_llm(observation, agent_reasoning, ground_truth)
                metric_b_raw = metric_b_result['score']
                metric_b_normalized = metric_b_raw / 5.0

                # 4. final score
                final_score = (0.5 * metric_a_score) + (0.5 * metric_b_normalized)

                if SHOW_DETAILED_OUTPUT:
                    scenario_text = Text(f"Scenario: {scenario}", style="bold magenta")

                    obs_panel = Panel(observation, title="Observation State", border_style="blue")

                    agent_content = f"Predicted Roles: {json.dumps(predicted_roles, indent=2)}\n\nReasoning:\n{agent_reasoning}"
                    agent_panel = Panel(agent_content, title=f"Agent Response ({agent_name})", border_style="green")

                    judge_content = f"Score: {metric_b_raw}/5.0\nExplanation: {metric_b_result['explanation']}"
                    judge_panel = Panel(judge_content, title="Judge Evaluation", border_style="yellow")

                    details = Group(
                        scenario_text,
                        Text(""),
                        obs_panel,
                        agent_panel,
                        judge_panel
                    )

                    console.print(Panel(details, title=f"Case {case_id} Analysis", border_style="white", expand=False))

                result_entry = {
                    "case_id": case_id,
                    "scenario": scenario,
                    "agent": agent_name,
                    "metric_a_score": metric_a_score,
                    "metric_b_raw": metric_b_raw,
                    "metric_b_normalized": metric_b_normalized,
                    "final_score": final_score,
                    "predicted_roles": predicted_roles,
                    "ground_truth_roles": ground_truth['roles'],
                    "agent_reasoning": agent_reasoning,
                    "judge_explanation": metric_b_result['explanation'],
                    "raw_response": response_raw
                }
                agent_results.append(result_entry)

                progress.advance(task)

        table = Table(title=f"Results for {agent_name}")
        table.add_column("Case ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Scenario", style="magenta")
        table.add_column("Metric A", justify="right", style="green")
        table.add_column("Metric B (Norm)", justify="right", style="blue")
        table.add_column("Final Score", justify="right", style="bold yellow")

        avg_final = 0
        for res in agent_results:
            table.add_row(
                str(res['case_id']),
                res['scenario'][:50] + "...",
                f"{res['metric_a_score']:.2f}",
                f"{res['metric_b_normalized']:.2f}",
                f"{res['final_score']:.2f}"
            )
            avg_final += res['final_score']

        if agent_results:
            avg_final /= len(agent_results)

        console.print(table)
        console.print(f"[bold]Average Final Score for {agent_name}: {avg_final:.2f}[/bold]")

        avg_metric_a = sum(r['metric_a_score'] for r in agent_results) / len(agent_results) if agent_results else 0
        avg_metric_b = sum(r['metric_b_normalized'] for r in agent_results) / len(agent_results) if agent_results else 0

        all_agent_results.append({
            "agent_name": agent_name,
            "summary": {
                "total_cases": len(agent_results),
                "avg_metric_a": round(avg_metric_a, 4),
                "avg_metric_b_normalized": round(avg_metric_b, 4),
                "avg_final_score": round(avg_final, 4),
            },
            "test_cases": agent_results
        })

    benchmark_output = {
        "benchmark_info": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_agents_tested": len(agents_to_test),
            "total_test_cases": len(test_cases),
        },
        "overall_summary": {
            agent_result["agent_name"]: agent_result["summary"]
            for agent_result in all_agent_results
        },
        "agent_results": all_agent_results
    }

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_file = os.path.join(results_dir, f"benchmark_results_{timestamp}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(benchmark_output, f, indent=2)

    console.print(f"\n[green]Detailed results saved to {output_file}[/green]")


if __name__ == "__main__":
    run_benchmark()
