import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.schemas import RevacMemory, EvaluationResponse
from src.config import OPENAI_API_KEY
from src.utils import get_model
from .base import Agent
from src.prompts.revac2_1_prompts import memory_module_prompt
from src.prompts.revac8_prompts import tone_selector_prompt, final_action_prompt_with_tone
from src.prompts.revac_prompts import reviewer_prompt, parse_sys_prompt


class Revac8Agent(Agent):
    """
    Revac agent with persistent memory and dynamic tone selection.

    Architecture:
    1. Update memory with new observation
    2. Pass memory + observation to reviewer agent
    3. Select optimal tone/style based on review + observation
    4. Pass observation + review + tone to action agent
    5. Return final action
    """

    def __init__(self, model_name: str, model_provider: str):
        super().__init__()
        self.model_name = model_name
        self.model_provider = model_provider
        self.model = get_model(model_name, model_provider)

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

        try:
            json_data = json.loads(res.content)
            updated_memory = RevacMemory(**json_data)
            self.memory = updated_memory
            return updated_memory
        except Exception as e:
            print(f"Error updating memory: {e}")
            print(f"Raw response: {res.content}")
            return self.memory

    def select_tone(self, observation: str, detailed_review: str) -> str:
        """
        Selects optimal tone and style for the current turn.

        Args:
            observation (str): Current game observation state
            detailed_review (str): Review from the reviewer agent

        Returns:
            str: Concise tone/style instruction or action reminder
        """
        model_tone = ChatOpenAI(
            model="gpt-5-nano",
            api_key=OPENAI_API_KEY
        )

        sys = SystemMessage(content=tone_selector_prompt)
        user = HumanMessage(
            content=f"# Detailed Review:\n{detailed_review}\n\n# Current Observation State:\n{observation}"
        )
        prompt = [sys, user]

        res = model_tone.invoke(prompt)

        return res.content.strip()

    def __call__(self, observation: str) -> str:
        """
        Main agent call - updates memory, gets review, selects tone, then action.

        Args:
            observation (str): Current observation state of the game

        Returns:
            str: Action to take in the game
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
        detailed_review = res.content
        print("Detailed Review:", detailed_review)
        tone_instruction = self.select_tone(observation, detailed_review)
        print("Selected Tone Instruction:", tone_instruction)   
        modified_action_prompt = final_action_prompt_with_tone.replace(
            "{dynamic_tone_and_style_instructions}",
            tone_instruction
        )

        sys = SystemMessage(content=modified_action_prompt)
        user = HumanMessage(
            content=f"# Here is the observation state:\n\n{observation}\n\n"
                    f"# Following is the detailed review:\n\n{detailed_review}"
        )
        prompt = [sys, user]
        final_res = self.model.invoke(prompt)
        print("Final Action Response:", final_res)
        return final_res.content

    def evaluate(self, observation: str) -> EvaluationResponse:
        """
        Agent's response to evaluate on benchmarking framework.
        Updates memory first, then evaluates with memory context.
        Note: Does NOT use tone selector (only for gameplay).

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

        try:
            json_data = json.loads(res_parse.content)
            result = EvaluationResponse(**json_data)
            print(result)
            return result
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Raw response: {res_parse.content}")
            raise


