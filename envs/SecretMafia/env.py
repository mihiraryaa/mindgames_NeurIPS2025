# Final Corrected envs/SecretMafia/env.py

from enum import Enum
import re, random
from typing import Tuple, Dict, Optional, List
import textarena as ta

class Phase(Enum):
    NIGHT_MAFIA = "Night-Mafia"
    NIGHT_DOCTOR = "Night-Doctor"
    NIGHT_DETECTIVE = "Night-Detective"
    DAY_DISCUSSION = "Day-Discussion"
    DAY_VOTING = "Day-Voting"

class Role:
    name: str = "Role"
    team: str = "Unknown"
    description: str = ""
    def get_prompt(self, player_id: int, player_roles: Dict[int, str], num_players: int, num_discussion_rounds: int) -> str: raise NotImplementedError

class Villager(Role):
    name = "Villager"
    team = "Village"
    description = "A regular villager. Your goal is to identify and eliminate all Mafia members through voting during the day."
    def get_prompt(self, player_id, player_roles, num_players, num_discussion_rounds):
        return (
            f"Welcome to Secret Mafia! You are Player {player_id}.\n"
            f"Your role: {self.name}\nTeam: {self.team}\nDescription: {self.description}\n\n"
            f"Players: {', '.join([f'Player {i}' for i in range(num_players)])}\n\n"
            f"The game progresses through Day and Night phases.\n"
            f"- During the Day phase, there are {num_discussion_rounds} rounds of discussion followed by voting.\n"
            f"- During discussions, everything you say is automatically broadcasted to all players.\n"
            f"- After discussions, all players must vote to eliminate one player.\n"
            f"- During the Night phase, you have no special actions.\n\n"
            f"The game ends when either all Mafia members are eliminated (Village wins) or\n"
            f"Mafia members equal or outnumber Villagers (Mafia wins).\n"
        )

class Mafia(Role):
    name = "Mafia"
    team = "Mafia"
    description = "A Mafia member. Eliminate villagers and gain majority."
    def get_prompt(self, player_id, player_roles, num_players, num_discussion_rounds):
        teammates = [f"Player {pid}" for pid, r in player_roles.items() if r == "Mafia"]
        return (
            f"Welcome to Secret Mafia! You are Player {player_id}.\n"
            f"Your role: {self.name}\nTeam: {self.team}\nDescription: {self.description}\n\n"
            f"Players: {', '.join([f'Player {i}' for i in range(num_players)])}\n\n"
            f"Your teammates are: {', '.join(teammates)}.\n\n"
            f"During DAY phase: Speak freely and vote.\n"
            f"During NIGHT phase: '[Player X]' to vote and eliminate a villager.\n"
            f"Win by eliminating villagers until Mafia equal or outnumber them.\n"
        )

class Doctor(Role):
    name = "Doctor"
    team = "Village"
    description = "Protect one player each night from Mafia elimination."
    def get_prompt(self, player_id, player_roles, num_players, num_discussion_rounds):
        return (
            f"Welcome to Secret Mafia! You are Player {player_id}.\n"
            f"Your role: {self.name}\nTeam: {self.team}\nDescription: {self.description}\n\n"
            f"Players: {', '.join([f'Player {i}' for i in range(num_players)])}\n\n"
            f"During DAY phase: Speak freely and vote.\n"
            f"During NIGHT phase: '[Player X]' to protect a player.\n"
            f"Win by identifying and eliminating all Mafia members.\n"
        )

class Detective(Role):
    name = "Detective"
    team = "Village"
    description = "Investigate players to find Mafia members."
    def get_prompt(self, player_id, player_roles, num_players, num_discussion_rounds):
        return (
            f"Welcome to Secret Mafia! You are Player {player_id}.\n"
            f"Your role: {self.name}\nTeam: {self.team}\nDescription: {self.description}\n\n"
            f"Players: {', '.join([f'Player {i}' for i in range(num_players)])}\n\n"
            f"During DAY phase: Speak freely and vote.\n"
            f"During NIGHT phase: '[Player X]' to investigate.\n"
            f"You'll learn immediately if the target is Mafia.\n"
            f"Win by identifying and eliminating all Mafia members.\n"
        )

class VoteHandler:
    @staticmethod
    def parse(text: str) -> Optional[int]:
        m = SecretMafiaEnv.voting_pattern.search(text)
        return int(m.group(1)) if m else None
    @staticmethod
    def tally(votes: Dict[int, int]) -> Optional[int]:
        if not votes: return None
        counts: Dict[int, int] = {}
        for target in votes.values():
            counts[target] = counts.get(target, 0) + 1
        top_score = max(counts.values())
        top_players = [pid for pid, c in counts.items() if c == top_score]
        return random.choice(top_players)

class SecretMafiaEnv(ta.Env):
    voting_pattern = re.compile(r".*\[(?:player\s*)?(\d+)\].*", re.IGNORECASE)
    _ROLE_FACTORY = {
        "Villager":  Villager,
        "Mafia":     Mafia,
        "Doctor":    Doctor,
        "Detective": Detective,
    }
    def __init__(self, mafia_ratio: float = 0.25, discussion_rounds: int = 3):
        self.mafia_ratio = mafia_ratio
        self.discussion_rounds = discussion_rounds

    def reset(self, num_players: int, seed: Optional[int] = None):
        assert 6 <= num_players <= 15, "Player count must be between 5 and 15."
        self.state = ta.TeamMultiPlayerState(num_players=num_players, seed=seed)
        self._assign_roles(num_players)
        self.phase: Phase = Phase.NIGHT_MAFIA
        game_state = {
            "phase": self.phase,
            "day_number": 1,
            "alive_players": list(range(num_players)),
            "player_roles": self.player_roles,
            "num_discussion_rounds": self.discussion_rounds,
            "votes": {},
            "pending_elimination": None,
        }
        self.state.reset(game_state=game_state, player_prompt_function=self._prompt, secret_roles=self.player_roles)
        self._send_phase_prompts()
        if self.next_player_ids:
            self.state.manually_set_current_player_id(self.next_player_ids.pop())
    
    def _assign_roles(self, num_players: int):
        self.player_roles = {}
        self.roles = {}
        num_mafia = max(1, round(num_players * self.mafia_ratio))
        role_pool = ["Mafia"] * num_mafia + ["Doctor", "Detective"] 
        role_pool += ["Villager"] * (num_players - len(role_pool))
        random.shuffle(role_pool)

        for pid, r_name in enumerate(role_pool):
            self.player_roles[pid] = r_name
            self.roles[pid] = self._ROLE_FACTORY[r_name]()

    def _prompt(self, player_id: int, game_state: dict) -> str:
        role_obj = self.roles[player_id]
        return role_obj.get_prompt(player_id = player_id, player_roles = self.player_roles, num_players = self.state.num_players, num_discussion_rounds = self.discussion_rounds)

    def step(self, action: str) -> Tuple[bool, ta.Info]:
        pid = self.state.current_player_id
        phase_dispatch = {
            Phase.DAY_DISCUSSION: self._handle_discussion, Phase.DAY_VOTING: self._handle_day_vote, Phase.NIGHT_MAFIA: self._handle_mafia_vote, 
            Phase.NIGHT_DOCTOR: self._handle_doctor_action, Phase.NIGHT_DETECTIVE: self._handle_detective_action,
        }
        phase_dispatch[self.phase](pid, action)
        
        # Centralized check: only advance the turn if the game is NOT over
        if not self.state.is_done:
            self._after_player_action()
            
        return self.state.step(rotate_player=False)

    def _after_player_action(self):
        if self.state.made_invalid_move:
            return

        # If there are still players in the queue for the current phase, rotate to the next one
        if self.next_player_ids:
            self.state.manually_set_current_player_id(self.next_player_ids.pop())
            return

        # If the queue is empty, the phase is over. Resolve the phase and set up the next one.
        if self.phase == Phase.DAY_VOTING:
            self._resolve_day_votes()
        elif self.phase == Phase.NIGHT_MAFIA:
            self._store_mafia_target()
        elif self.phase in (Phase.NIGHT_DOCTOR, Phase.NIGHT_DETECTIVE):
            if self._compute_next_phase() == Phase.DAY_DISCUSSION:
                self._resolve_night_outcome()
        
        # If the last action ended the game, stop here.
        if self.state.is_done:
            return

        # Transition to the next phase
        self.phase = self._compute_next_phase()
        self.state.game_state["phase"] = self.phase
        self._send_phase_prompts()

        # If the new phase has players, set the next player. Otherwise, the game ends.
        if self.next_player_ids:
            self.state.manually_set_current_player_id(self.next_player_ids.pop())
        elif not self.state.is_done:
             self._check_win() # Fallback win condition check

    def _compute_next_phase(self) -> Phase:
        doctor_alive     = any(self.player_roles[p] == "Doctor"    for p in self.state.game_state["alive_players"])
        detective_alive  = any(self.player_roles[p] == "Detective" for p in self.state.game_state["alive_players"])
        match self.phase:
            case Phase.NIGHT_MAFIA:     return Phase.NIGHT_DOCTOR if doctor_alive else (Phase.NIGHT_DETECTIVE if detective_alive else Phase.DAY_DISCUSSION)
            case Phase.NIGHT_DOCTOR:    return Phase.NIGHT_DETECTIVE if detective_alive else Phase.DAY_DISCUSSION
            case Phase.NIGHT_DETECTIVE: return Phase.DAY_DISCUSSION
            case Phase.DAY_DISCUSSION:  return Phase.DAY_VOTING
            case Phase.DAY_VOTING:      return Phase.NIGHT_MAFIA
            case _:                     raise RuntimeError("Unknown phase")

    def _send_phase_prompts(self):
        gs = self.state.game_state
        alive = gs["alive_players"]
        self.next_player_ids: List[int] = []

        if self.phase == Phase.NIGHT_MAFIA:
            mafia = [p for p in alive if self.player_roles[p] == "Mafia"]
            if mafia:
                targets = [p for p in alive if p not in mafia]
                if targets:
                    for p in mafia:
                        self.state.add_observation(to_id=p, message=f"Night has fallen. Mafia, agree on a victim.\nValid targets: {', '.join(f'[{t}]' for t in targets)}", observation_type=ta.ObservationType.GAME_MESSAGE)
                    self.next_player_ids = random.sample(mafia, k=len(mafia))

        elif self.phase == Phase.NIGHT_DOCTOR:
            if any(self.player_roles[p] == "Doctor" for p in alive):
                doc = next(p for p in alive if self.player_roles[p] == "Doctor")
                opts = ", ".join(f"[{t}]" for t in alive if t != doc)
                if opts:
                    self.state.add_observation(to_id=doc, message=f"Night phase - choose one player to protect: {opts}", observation_type=ta.ObservationType.GAME_MESSAGE)
                    self.next_player_ids = [doc]

        elif self.phase == Phase.NIGHT_DETECTIVE:
            if any(self.player_roles[p] == "Detective" for p in alive):
                det = next(p for p in alive if self.player_roles[p] == "Detective")
                opts = ", ".join(f"[{t}]" for t in alive if t != det)
                if opts:
                    self.state.add_observation(to_id=det, message=f"Night phase - choose one player to investigate: {opts}", observation_type=ta.ObservationType.GAME_MESSAGE)
                    self.next_player_ids = [det]

        elif self.phase == Phase.DAY_DISCUSSION:
            if alive:
                rounds = self.discussion_rounds
                self.state.add_observation(to_id=-1, message=f"Day breaks. Discuss for {rounds} rounds, then a vote will follow.", observation_type=ta.ObservationType.GAME_MESSAGE)
                players = random.sample(alive, k=len(alive))
                self.next_player_ids = players * rounds

        elif self.phase == Phase.DAY_VOTING:
            if alive:
                opts = ", ".join(f"[{p}]" for p in alive)
                self.state.add_observation(to_id=-1, message=f"Voting phase - submit one vote in format [X]. Valid: {opts}", observation_type=ta.ObservationType.GAME_MESSAGE)
                self.next_player_ids = random.sample(alive, k=len(alive))

    def _handle_discussion(self, pid: int, action: str):
        self.state.add_observation(from_id=pid, message=action, observation_type=ta.ObservationType.PLAYER_ACTION)
    def _handle_day_vote(self, pid: int, action: str):
        self._record_vote(pid, action, broadcast_to_all=True)
    def _handle_mafia_vote(self, pid: int, action: str):
        self._record_vote(pid, action, broadcast_to_mafia_only=True)
    def _handle_doctor_action(self, pid: int, action: str):
        target = VoteHandler.parse(action)
        if target is None or target not in self.state.game_state["alive_players"]:
            self._mark_invalid(pid, "Invalid protection target.")
            return
        if target == self.state.game_state["pending_elimination"]:
            self.state.game_state["pending_elimination"] = None
        self.state.add_observation(from_id=pid, to_id=pid, message=action, observation_type=ta.ObservationType.PLAYER_ACTION)
    def _handle_detective_action(self, pid: int, action: str):
        target = VoteHandler.parse(action)
        if target is None or target not in self.state.game_state["alive_players"]:
            self._mark_invalid(pid, "Invalid investigation target.")
            return
        is_mafia = self.player_roles[target] == "Mafia"
        result = f"Player {target} IS{' ' if is_mafia else ' NOT '}a Mafia member."
        self.state.add_observation(to_id=pid, message=result, observation_type=ta.ObservationType.GAME_MESSAGE)

    def _record_vote(self, pid: int, action: str, *, broadcast_to_all=False, broadcast_to_mafia_only=False):
        target = VoteHandler.parse(action)
        if target is None or target not in self.state.game_state["alive_players"]:
            self._mark_invalid(pid, "Vote not in valid format or invalid target.")
            return
        self.state.game_state["votes"][pid] = target
        if broadcast_to_all:
            self.state.add_observation(from_id=pid, message=action, observation_type=ta.ObservationType.PLAYER_ACTION)
        elif broadcast_to_mafia_only:
            mafia = [p for p in self.state.game_state["alive_players"] if self.player_roles[p] == "Mafia"]
            for m in mafia:
                self.state.add_observation(from_id=pid, to_id=m, message=action, observation_type=ta.ObservationType.PLAYER_ACTION)

    def _mark_invalid(self, pid: int, reason: str):
        if self.state.set_invalid_move(reason):
            self._eliminate_player(pid, "has been eliminated for making too many invalid moves.")
    
    def _resolve_day_votes(self):
        target = VoteHandler.tally(self.state.game_state["votes"])
        self.state.game_state["votes"].clear()
        if target is not None:
            self._eliminate_player(target, "was eliminated by vote")
        else:
            self.state.add_observation(message="No consensus - nobody was eliminated.", observation_type=ta.ObservationType.GAME_MESSAGE)

    def _store_mafia_target(self):
        self.state.game_state["pending_elimination"] = VoteHandler.tally(self.state.game_state["votes"])
        self.state.game_state["votes"].clear()

    def _resolve_night_outcome(self):
        tgt = self.state.game_state["pending_elimination"]
        self.state.game_state["pending_elimination"] = None
        if tgt is not None:
            self._eliminate_player(tgt, "was killed during the night")
        else:
            self.state.add_observation(message="No one was killed tonight.", observation_type=ta.ObservationType.GAME_MESSAGE)

    def _eliminate_player(self, pid: int, reason: str):
        if pid in self.state.game_state["alive_players"]:
            self.state.game_state["alive_players"].remove(pid)
        self.state.add_observation(message=f"Player {pid} {reason}.", observation_type=ta.ObservationType.GAME_MESSAGE)
        self._check_win()

    def _check_win(self):
        if self.state.is_done: return
        alive = self.state.game_state["alive_players"]
        mafia_alive = [p for p in alive if self.player_roles[p] == "Mafia"]
        if not mafia_alive:
            villagers = [p for p in range(self.state.num_players) if self.player_roles[p] != "Mafia"]
            self.state.set_winners(player_ids=villagers, reason="All Mafia were eliminated. Village wins!")
        elif len(mafia_alive) * 2 >= len(alive):
            mafia = [p for p in range(self.state.num_players) if self.player_roles[p] == "Mafia"]
            self.state.set_winners(player_ids=mafia, reason="Mafia reached parity with villagers. Mafia wins!")