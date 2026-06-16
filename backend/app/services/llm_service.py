import json
import time
import logging
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger("EcoRefactor.services.llm_service")


def _clean_explanations(explanations: list[str]) -> list[str]:
    cleaned: list[str] = []
    for item in explanations:
        text = str(item).replace("**", "").replace("`", "").strip()
        if ":" in text and len(text.split(":", 1)[0].split()) <= 4:
            text = text.split(":", 1)[1].strip()
        text = " ".join(text.split())
        if text:
            cleaned.append(text)
    return cleaned[:4]

def refactor_code_with_gemini(source_code: str) -> dict:
    """
    Sends python code to Gemini for optimization.
    Returns a structured optimization suggestion payload.
    """
    if not settings.is_gemini_configured:
        logger.warning("Gemini API Key not configured. Using mock refactoring fallback.")
        return {
            "optimized_code": source_code + "\n\n# Suggested review: simplify repeated work if this path becomes hot.\n",
            "explanations": [
                "AI optimization is unavailable because the Gemini API key is missing.",
                "Add GEMINI_API_KEY in backend/app/core/.env to enable suggestions.",
            ],
            "risk_level": "low",
            "confidence": "low",
            "expected_runtime_impact": "unknown",
            "expected_memory_impact": "unknown",
            "expected_scalability_impact": "unknown",
        }

    try:
        masked_key = settings.GEMINI_API_KEY[:4] + "..." + settings.GEMINI_API_KEY[-4:] if len(settings.GEMINI_API_KEY) > 8 else "..."
        logger.info(f"Initializing Gemini Client with key: {masked_key}")
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        prompt = f"""
You are an expert Python performance engineer and sustainability advisor. Your goal is to improve code efficiency while keeping the rewritten code simple, readable, and close to the user's original style.

Optimize the following Python code focusing on the following:
1. Vectorize slow element-wise loops using NumPy, PyTorch, or built-in list comprehensions.
2. Minimize redundant memory allocation and overhead (e.g., in-place operations, avoiding massive temporary lists).
3. Use lazy evaluation and Python generators (yield / generator expressions) for handling large streams of data.
4. Use standard library or custom caching mechanisms (like functools.lru_cache) to prevent repetitive calculations.
5. Improve algorithmic complexity (e.g., O(N^2) to O(N log N)) and I/O efficiency.

Important rewrite rules:
- Prefer the smallest useful improvement, not the most clever rewrite.
- Preserve the original function names and general structure where possible.
- Do not add docstrings, extensive comments, input validation, caching, decorators, or extra helper functions unless they are clearly necessary for performance.
- Avoid adding imports unless they are required for the optimization.
- If the optimization would make the code much harder to understand, keep the simpler version and say the impact is minimal.

---
Source Code:
{source_code}
---

Your response MUST be a valid JSON object with exactly these keys:
1. "optimized_code": string. The full rewritten Python code. No markdown fences.
2. "explanations": array of strings. Each string must be short, plain-English, and under 14 words. No markdown formatting, no labels like "Optimization 1".
3. "risk_level": one of "low", "medium", "high". Use "high" only if the rewrite may alter behavior or assumptions.
4. "confidence": one of "low", "medium", "high". This is your confidence that the optimization should help.
5. "expected_runtime_impact": one short phrase, for example "small improvement", "moderate improvement", "large improvement", or "unknown".
6. "expected_memory_impact": one short phrase, for example "lower peak memory", "similar memory", "higher memory", or "unknown".
7. "expected_scalability_impact": one short phrase, for example "better for repeated runs", "better for larger inputs", "minimal change", or "unknown".

Respond ONLY with the JSON document. Do not add conversational text.
"""
        
        logger.info("Sending code refactoring request to Gemini API (gemini-2.5-flash)...")
        gemini_start = time.perf_counter()
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        gemini_elapsed = time.perf_counter() - gemini_start
        logger.info(f"Received response from Gemini API in {gemini_elapsed:.4f} seconds")
        
        response_text = response.text
        # Clean potential markdown wrapping just in case
        if response_text.startswith("```json"):
            response_text = response_text.split("```json", 1)[1]
        if response_text.endswith("```"):
            response_text = response_text.rsplit("```", 1)[0]
        
        data = json.loads(response_text.strip())
        cleaned_explanations = _clean_explanations(data.get("explanations", ["Refactored for efficiency."]))
        result = {
            "optimized_code": data.get("optimized_code", source_code),
            "explanations": cleaned_explanations or ["Reduced repeated work with a simpler execution path."],
            "risk_level": data.get("risk_level", "medium"),
            "confidence": data.get("confidence", "medium"),
            "expected_runtime_impact": data.get("expected_runtime_impact", "unknown"),
            "expected_memory_impact": data.get("expected_memory_impact", "unknown"),
            "expected_scalability_impact": data.get("expected_scalability_impact", "unknown"),
        }

        logger.info(
            "Successfully processed refactoring response; returned optimized code (len=%s) and %s explanations",
            len(result["optimized_code"]),
            len(result["explanations"]),
        )
        return result

    except Exception as e:
        logger.error(f"Error communicating with Gemini API: {e}", exc_info=True)
        return {
            "optimized_code": source_code,
            "explanations": [f"Error during refactoring: {str(e)}"],
            "risk_level": "high",
            "confidence": "low",
            "expected_runtime_impact": "unknown",
            "expected_memory_impact": "unknown",
            "expected_scalability_impact": "unknown",
        }
