import json
import os
from typing import List, Optional

import httpx
from pydantic import BaseModel

from trader.exceptions import TraderException
from trader.models import Agent, AgentPayload, RegistrationResponsePayload


TOKEN_PATH = ".token"
BASE_URL = 'https://api.spacetraders.io/v2'


class RegistrationFields(BaseModel):
    call_sign: str
    faction: str

class Trader:
    api_key: Optional[str]

    def __init__(self) -> None:
        if os.path.exists(TOKEN_PATH):
            print("Registration valid, proceeding")
            with open(TOKEN_PATH, "r") as file:
                self.api_key = file.read()
        else:
            raise TraderException("No API key found in path, error!")
        

    def register(self, data: RegistrationFields) -> None:
        if self.api_key:
            return

        response = httpx.post(f"{BASE_URL}/register", json=data.model_dump_json())
        response_dict = json.loads(response.content)
        payload = RegistrationResponsePayload(**response_dict)

        with open(TOKEN_PATH, "w") as file:
            file.write(payload.data.token)

    def agent(self) -> None:
        bearer = f"Bearer {self.api_key}".replace("\n", "")
        response = httpx.get(f"{BASE_URL}/my/agent", headers={"Authorization": bearer})
        agent_response: AgentPayload | List[AgentPayload] = AgentPayload.from_json(response.content)
        if isinstance(agent_response, List):
            agent_response = agent_response[0]
        agent: Agent = agent_response.data
        print(f"Found agent (symbol): {agent.symbol}")

