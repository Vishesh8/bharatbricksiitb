import asyncio
import logging

import mlflow
from dotenv import load_dotenv

from agent_server.config import MODEL_ENDPOINT
from mlflow.genai.agent_server import get_invoke_function
from mlflow.genai.scorers import (
    Completeness,
    ConversationalSafety,
    ConversationCompleteness,
    Fluency,
    KnowledgeRetention,
    RelevanceToQuery,
    Safety,
    ToolCallCorrectness,
    UserFrustration,
)
from mlflow.genai.simulators import ConversationSimulator
from mlflow.types.responses import ResponsesAgentRequest

load_dotenv(dotenv_path=".env", override=True)
logging.getLogger("mlflow.utils.autologging_utils").setLevel(logging.ERROR)

from agent_server import agent  # noqa: F401, E402

test_cases = [
    {
        "goal": "Find out what students think about hostel food quality at IIT Bombay",
        "persona": "A JEE aspirant who just got their rank and is deciding between IITs.",
        "simulation_guidelines": [
            "Ask about mess food quality first, then ask about alternatives on campus.",
            "Prefer short messages",
        ],
    },
    {
        "goal": "Understand the placement scene for CS students at IIT Bombay",
        "persona": "A second-year student considering switching branches to CS.",
        "simulation_guidelines": [
            "Ask about average packages first, then ask about the preparation process.",
            "Use casual language",
        ],
    },
    {
        "goal": "Learn about campus culture, fests, and student life at IIT Bombay",
        "persona": "A freshie who just joined and wants to know how to make the most of insti life.",
        "simulation_guidelines": [
            "Ask about the major fests first, then about clubs and extracurriculars.",
            "Ask follow-up questions about how to get involved",
        ],
    },
    {
        "goal": "Get advice on how to handle academic pressure and avoid getting an FR",
        "persona": "A struggling sophomore who is worried about their GPA.",
        "simulation_guidelines": [
            "Express anxiety about upcoming exams, then ask for study strategies.",
            "Ask about what happens if you get an FR",
        ],
    },
]

simulator = ConversationSimulator(
    test_cases=test_cases,
    max_turns=5,
    user_model=f"databricks:/{MODEL_ENDPOINT}",
)

invoke_fn = get_invoke_function()
assert invoke_fn is not None, (
    "No function registered with the `@invoke` decorator found. "
    "Ensure you have a function decorated with `@invoke()`."
)

if asyncio.iscoroutinefunction(invoke_fn):
    import nest_asyncio

    nest_asyncio.apply()

    def predict_fn(input: list[dict], **kwargs) -> dict:
        req = ResponsesAgentRequest(input=input)
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(invoke_fn(req))
        return response.model_dump()
else:

    def predict_fn(input: list[dict], **kwargs) -> dict:
        req = ResponsesAgentRequest(input=input)
        response = invoke_fn(req)
        return response.model_dump()


def evaluate():
    mlflow.genai.evaluate(
        data=simulator,
        predict_fn=predict_fn,
        scorers=[
            Completeness(),
            ConversationCompleteness(),
            ConversationalSafety(),
            KnowledgeRetention(),
            UserFrustration(),
            Fluency(),
            RelevanceToQuery(),
            Safety(),
            ToolCallCorrectness(),
        ],
    )
