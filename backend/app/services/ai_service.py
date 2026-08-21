import asyncio
import importlib.util
from pathlib import Path
from typing import Any


def _load_process_message():
    project_root = Path(__file__).resolve().parents[3]
    module_path = project_root / "ai" / "Ai_module.py"
    spec = importlib.util.spec_from_file_location("smart_campus_ai_chatbot", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Existing AI assistant module could not be loaded.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.process_message


async def process_chat_message(message: str) -> dict[str, Any]:
    process_message = await asyncio.to_thread(_load_process_message)
    return await asyncio.to_thread(process_message, message)