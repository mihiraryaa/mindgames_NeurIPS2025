import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.prompts.revac_prompts import reviewer_prompt, final_action_prompt, parse_sys_prompt
from src.config import OPENAI_API_KEY, GROQ_API_KEY
from src.utils import get_model
from .base import Agent
from src.agents.schemas import EvaluationResponse


class RevacAgent(Agent):
    """
    Revac agent with two-stage architecture.

    Architecture:
    1. Pass observation to reviewer agent
    2. Pass observation + review to action agent
    3. Return final action
    """
    
    def __init__(self, model_name:str, model_provider: str):
        super().__init__()       
        self.model_name = model_name
        self.model_provider = model_provider
        self.model = get_model(model_name, model_provider)
    
    def __call__(self, observation: str) -> str:
        """
        Main agent call - gets review, then action.

        Args:
            observation (str): Current observation state of the game

        Returns:
            str: Action to take in the game
        """
        
        sys=SystemMessage(content=reviewer_prompt)
        user=HumanMessage(content=f"# Here is the observation state: \n\n {observation}")
        prompt=[sys,user]
        
        model=self.model
        res=model.invoke(prompt)

    
       # print(res.content)

        # now calling the final action agent
        detailed_review=res.content
        sys=SystemMessage(content=final_action_prompt)
        user=HumanMessage(content=f"# Here is the observation state: \n\n {observation}\n\n # Following is the detailed review: \n\n{detailed_review}")
        prompt=[sys, user]
        final_res=model.invoke(prompt)

        

        return final_res.content
    
    def evaluate(self, observation: str) -> EvaluationResponse:
        """
        Agent's response to evaluate on benchmarking framework.

        Args:
            observation (str): The observation state of the game

        Returns:
            EvaluationResponse: {
                "roles": Dict[str, str],
                "explanation": str
            }
        """
        import json

        ## calling the reviewer agent
        sys=SystemMessage(content=reviewer_prompt)
        user=HumanMessage(content=f"# Here is the observation state: \n\n {observation}")
        prompt=[sys,user]
        model=self.model
        res=model.invoke(prompt)

        
        model_parse=ChatOpenAI(
            model="gpt-5-nano",
            api_key=OPENAI_API_KEY,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

        parse_sys=SystemMessage(content=parse_sys_prompt)
        parse_user=HumanMessage(content=res.content)
        parse_prompt=[parse_sys, parse_user]
        res_parse=model_parse.invoke(parse_prompt)

        try:
            json_data = json.loads(res_parse.content)
            result = EvaluationResponse(**json_data)
            print(result)
            return result
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Raw response: {res_parse.content}")
            raise

  



