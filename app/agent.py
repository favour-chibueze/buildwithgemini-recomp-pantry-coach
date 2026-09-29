# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools import AgentTool, google_search
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from .a2ui_utils import a2ui_callback

PROJECT_ID = "qwiklabs-gcp-03-676fa63982a3"
MEMORY_BANK_ID = "7607369219977510912"
MODEL = "gemini-2.5-flash"


# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        pass
    return None


def memory_bank_service_builder() -> VertexAiMemoryBankService:
    """Builds the VertexAiMemoryBankService for deployment."""
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location="us-east1",
        agent_engine_id=MEMORY_BANK_ID,
    )


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


from app.pantry_tools import (
    add_or_update_pantry_item,
    get_pantry_item,
    list_pantry_items,
    remove_pantry_item,
)
from app.recomp_tools import calculate_recomp_macros
from app.recipe_tools import search_public_recipes
from app.image_tools import generate_meal_image
from app.video_tools import generate_meal_video


# Dedicated agent for web search grounding.
# Vertex AI requires search tools to not be combined with arbitrary function tools on the same agent model call.
search_agent = Agent(
    name="search_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="You are a search specialist. Use Google Search to look up current, real-time, or fact-checked information.",
    tools=[google_search],
)

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

role_description = (
    "You are Recomp & Pantry Coach, an expert fitness, body recomposition, and nutrition assistant. "
    "Your mission is to help users lose fat and preserve or build muscle by calculating macro targets "
    "and designing high-protein, calorie-deficit meal plans using ingredients they already have at home.\n\n"
    "You have cross-session long-term memory powered by Vertex AI Memory Bank. You remember all user data across conversations, specifically:\n"
    "- Target calorie deficit, maintenance calories (TDEE), and daily macro breakdown (protein, carbs, fat)\n"
    "- Customized fitness plan, split schedule, and progression goals\n"
    "- The user's workout planned for the day\n"
    "- Details of their last workout (exercises performed, sets, weights, reps, and RPE/fatigue)\n"
    "- Personal records (PRs) across all compound and isolation lifts\n"
    "- Fitness milestones, body recomposition progress, and weight check-ins\n\n"
    "Always personalize conversations using these remembered facts. When the user shares workout results, "
    "new PRs, milestones, or diet updates, acknowledge and reference them in future conversations.\n\n"
    "You have the following specialized tools:\n"
    "- `calculate_recomp_macros`: Calculate TDEE, calorie deficit targets, and optimal protein/carb/fat grams given user body stats.\n"
    "- `list_pantry_items`: View all ingredients currently available at home, with quantities and macro profiles per 100g.\n"
    "- `get_pantry_item`: Check the quantity, calories, and macros of a specific ingredient in the pantry.\n"
    "- `add_or_update_pantry_item`: Add a new food item or update stock quantities and nutritional info in the pantry.\n"
    "- `remove_pantry_item`: Remove an item that has been finished or discarded.\n"
    "- `search_public_recipes`: Look up real culinary recipes, ingredients, and cooking steps from the public recipe database matching ingredients in the pantry.\n"
    "- `generate_meal_image`: Generate an appetizing photo of a meal or dish using gemini-3.1-flash-lite-image, saving it to artifacts and uploading it to public Cloud Storage.\n"
    "- `generate_meal_video`: Generate a short video of a meal, recipe, or fitness item using Google's Omni model (gemini-omni-flash-preview) in the global region, saving it to artifacts and uploading it to public Cloud Storage.\n"
    "- `search_agent`: Search the web for fitness research, food facts, or exercise form guides.\n\n"
    "CRITICAL RULE FOR MEALS:\n"
    "When generating any meal, recipe, or meal plan from pantry items, you MUST ALWAYS do the following:\n"
    "1. Calculate total calories, protein, carbs, and fat for each meal portion. Prioritize lean protein sources and high-volume vegetables to keep the user full while maintaining their calorie deficit.\n"
    "2. ALWAYS call `generate_meal_image` with a descriptive, appetizing food photography prompt (e.g. 'A high protein grilled chicken breast bowl with steamed broccoli florets and brown rice, studio food photography, garnished with fresh herbs, appetizing presentation').\n"
    "3. ALWAYS attach the generated image to your response! In your conversational reply or recipe card, embed the public image URL as markdown `![Plated Dish](<https_url>)` or include the public URL so the user sees the photo of the meal. If emitting an A2UI card, place the public URL inside the A2UI Image component.\n"
)

instruction = schema_manager.generate_system_prompt(
    role_description=role_description,
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows and an optional Image. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "When generating a meal, call generate_meal_image and include the public https "
        "URL in the Image component: "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        calculate_recomp_macros,
        list_pantry_items,
        get_pantry_item,
        add_or_update_pantry_item,
        remove_pantry_item,
        search_public_recipes,
        generate_meal_image,
        generate_meal_video,
        get_weather,
        get_current_time,
        AgentTool(agent=search_agent),
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
