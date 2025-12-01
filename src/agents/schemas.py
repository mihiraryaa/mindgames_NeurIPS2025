from typing import Dict, List
from pydantic import BaseModel, Field

# schema for benchmarking evaluation response
class EvaluationResponse(BaseModel):
    roles: Dict[str, str] = Field(
        ...,
        description="A dictionary mapping player names to their deduced roles. Keys must be in format 'Player 0', 'Player 1', etc. Values must be one of: 'Villager', 'Mafia' only. Example: {'Player 0': 'Villager', 'Player 1': 'Mafia', 'Player 2': 'Villager', 'Player 3': 'Villager', 'Player 4': 'Mafia', 'Player 5': 'Villager'}"
    )
    explanation: str = Field(
        ...,
        description="Detailed reasoning behind the role deductions, citing specific observation states and player behaviors"
    )


# schema for agent's memory in revac2.1 and revac8
class SocialRelation(BaseModel):
    """Represents a single social interaction or role claim in the game"""
    player: str = Field(
        ...,
        description="The player making the action, formatted as 'Player 0', 'Player 1', etc."
    )
    relation: str = Field(
        ...,
        description="Type of relation: 'accuses', 'defends', or 'claims_role'"
    )
    target: str = Field(
        ...,
        description="The target player (e.g., 'Player 1') for accusations/support, or role name (e.g., 'Mafia', 'Detective') for role claims"
    )

class RevacMemory(BaseModel):
    """Memory schema for the Revac agent to track game state and player information"""
    player_profiles: str = Field(
        ...,
        description="String representation of player profiles including suspected role tendencies, credibility indicators and contradictions observed"
    )
    social_alignment_graph: List[SocialRelation] = Field(
        ...,
        description="List of social relations including accusations, support, defenses, and role claims. Example: [{'player': 'Player 0', 'relation': 'accuses', 'target': 'Player 1'}, {'player': 'Player 2', 'relation': 'claims_role', 'target': 'Detective'}]"
    )
    

