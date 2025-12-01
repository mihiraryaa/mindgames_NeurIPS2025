import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.schemas import RevacMemory, EvaluationResponse
from src.config import OPENAI_API_KEY
from src.utils import get_model
from .base import Agent
from src.prompts.revac2_1_prompts import memory_module_prompt, reviewer_prompt, final_action_prompt, parse_sys_prompt


class Revac2Agent(Agent):
    """
    Revac agent with persistent memory module.

    Architecture:
    1. Update memory with new observation
    2. Pass memory + observation to reviewer agent
    3. Pass observation + review to action agent
    4. Return final action
    """

    def __init__(self, model_name: str, model_provider: str):
        super().__init__()
        self.model_name = model_name
        self.model_provider = model_provider
        self.model = get_model(model_name, model_provider)

        # Initialize empty memory
        self.memory = RevacMemory(
            player_profiles="",
            social_alignment_graph=[]
        )

    def update_memory(self, observation: str) -> RevacMemory:
        """
        Updates the agent's memory based on new observation.

        Args:
            observation (str): Current game observation state

        Returns:
            RevacMemory: Updated memory object
        """
        model_memory = ChatOpenAI(
            model="gpt-4o",
            api_key=OPENAI_API_KEY,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

        current_memory_dict = {
            "player_profiles": self.memory.player_profiles,
            "social_alignment_graph": [
                {"player": rel.player, "relation": rel.relation, "target": rel.target}
                for rel in self.memory.social_alignment_graph
            ]
        }

        sys = SystemMessage(content=f"{memory_module_prompt}\n\nIMPORTANT: Output your response as a JSON object with 'player_profiles' and 'social_alignment_graph' fields.")
        user = HumanMessage(
            content=f"# Current Memory State:\n{json.dumps(current_memory_dict, indent=2)}\n\n"
                    f"# New Observation State:\n{observation}"
        )
        prompt = [sys, user]

        res = model_memory.invoke(prompt)

        # Parse JSON and validate with Pydantic
        try:
            json_data = json.loads(res.content)
            updated_memory = RevacMemory(**json_data)
            self.memory = updated_memory
            return updated_memory
        except Exception as e:
            print(f"Error updating memory: {e}")
            print(f"Raw response: {res.content}")
            # Return current memory if update fails
            return self.memory

    def __call__(self, observation: str) -> str:
        """
        Main agent call - updates memory, gets review, then action.

        Args:
            observation (str): Current observation state of the game

        Returns:
            str: Action to take in the game
        """
        # Update memory with new observation
        updated_memory = self.update_memory(observation)

        # memory converted to string for reviewer
        memory_str = f"""# Agent Memory:

## Player Profiles:
{updated_memory.player_profiles if updated_memory.player_profiles else "No profiles yet"}

## Social Alignment Graph:
{json.dumps([{"player": rel.player, "relation": rel.relation, "target": rel.target}
             for rel in updated_memory.social_alignment_graph], indent=2) if updated_memory.social_alignment_graph else "No relations recorded yet"}
"""

        sys = SystemMessage(content=reviewer_prompt)
        user = HumanMessage(
            content=f"{memory_str}\n\n# Current Observation State:\n{observation}"
        )
        prompt = [sys, user]

        res = self.model.invoke(prompt)
        detailed_review = res.content

        sys = SystemMessage(content=final_action_prompt)
        user = HumanMessage(
            content=f"# Here is the observation state:\n\n{observation}\n\n"
                    f"# Following is the detailed review:\n\n{detailed_review}"
        )
        prompt = [sys, user]
        final_res = self.model.invoke(prompt)

        return final_res.content

    def evaluate(self, observation: str) -> EvaluationResponse:
        """
        Agent's response to evaluate on benchmarking framework.
        Updates memory first, then evaluates with memory context.

        Args:
            observation (str): The observation state of the game

        Returns:
            EvaluationResponse: {
                "roles": Dict[str, str],
                "explanation": str
            }
        """
        
        updated_memory = self.update_memory(observation)

        memory_str = f"""# Agent Memory:

## Player Profiles:
{updated_memory.player_profiles if updated_memory.player_profiles else "No profiles yet"}

## Social Alignment Graph:
{json.dumps([{"player": rel.player, "relation": rel.relation, "target": rel.target}
             for rel in updated_memory.social_alignment_graph], indent=2) if updated_memory.social_alignment_graph else "No relations recorded yet"}
"""

        sys = SystemMessage(content=reviewer_prompt)
        user = HumanMessage(
            content=f"{memory_str}\n\n# Current Observation State:\n{observation}"
        )
        prompt = [sys, user]

        res = self.model.invoke(prompt)

        model_parse = ChatOpenAI(
            model="gpt-5-nano",
            api_key=OPENAI_API_KEY,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

        parse_sys = SystemMessage(content=parse_sys_prompt)
        parse_user = HumanMessage(content=res.content)
        parse_prompt = [parse_sys, parse_user]
        res_parse = model_parse.invoke(parse_prompt)

        # Parse JSON and validate with Pydantic
        try:
            json_data = json.loads(res_parse.content)
            result = EvaluationResponse(**json_data)
            print(result)
            return result
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Raw response: {res_parse.content}")
            raise



