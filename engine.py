import asyncio
import json
import os

from backboard import BackboardClient
from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL = os.getenv("GEMMA_MODEL", "gemma-3-4b-it")


def get_cleaning_suggestions(report, approved_rules=None):
    """Ask Gemma for suggestions; this function never edits the CSV."""
    api_key = os.getenv("GEMMA_API_KEY")
    if not api_key:
        return "GEMMA_API_KEY is missing. Check your .env file."

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are FixMyCSV, a data-cleaning assistant for small retail businesses.

Review this data-quality report and suggest practical next steps.

Rules:
- Never invent missing prices, quantities, or other business values.
- Never recommend silently deleting records.
- Treat possible duplicates and uncertain corrections as items for human review.
- Clearly distinguish safe formatting fixes from changes that need business approval.
- Explain each suggestion briefly.
- Do not claim that a correction has been verified when it has not.
- Return a short numbered list.
- Do not execute changes; only suggest them.

DATA-QUALITY REPORT:
{json.dumps(report, indent=2, ensure_ascii=True, default=str)}

PREVIOUSLY APPROVED BUSINESS RULES:
{json.dumps(approved_rules or [], indent=2, ensure_ascii=True, default=str)}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
        if not response.text:
            return "Gemma returned an empty response."
        return response.text.strip()
    except Exception as error:
        return f"Gemma request failed: {error}"


def _get_backboard_client():
    api_key = os.getenv("BACKBOARD_API_KEY")
    assistant_id = os.getenv("BACKBOARD_ASSISTANT_ID")

    if not api_key or not assistant_id:
        raise ValueError(
            "Configure BACKBOARD_API_KEY and BACKBOARD_ASSISTANT_ID in .env."
        )

    return BackboardClient(api_key=api_key), assistant_id


async def _save_cleaning_rule(rule):
    client, assistant_id = _get_backboard_client()
    return await client.add_memory(
        assistant_id=assistant_id,
        content=rule,
        metadata={
            "category": "retail_csv_cleaning_rule",
            "source": "user_approved",
        },
    )


def save_cleaning_rule(rule):
    try:
        return asyncio.run(_save_cleaning_rule(rule))
    except Exception as error:
        raise RuntimeError(f"Could not save cleaning rule: {error}") from error


async def _search_cleaning_rules(query):
    client, assistant_id = _get_backboard_client()
    result = await client.search_memories(
        assistant_id=assistant_id,
        query=query,
        limit=5,
    )
    return result.get("memories", [])


def search_cleaning_rules(query):
    try:
        return asyncio.run(_search_cleaning_rules(query))
    except Exception as error:
        raise RuntimeError(
            f"Could not retrieve cleaning rules: {error}"
        ) from error
