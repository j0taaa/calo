import json
import os
from typing import Any, Dict, List, Optional

from openai import BadRequestError, OpenAI

from agent.pdf_rag import build_context_snippet
from agent.web_tools import search_web


def _get_openai_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _get_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-5")


def _tool_schemas() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "search_web",
                "description": "Search the web for up-to-date information and return a list of results with title, url, and snippet.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "num_results": {"type": "integer", "minimum": 1, "maximum": 15},
                        "region": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_pdf",
                "description": "Search the indexed HCIP PDF and return the most relevant chunks to answer the question.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "top_k": {"type": "integer", "minimum": 1, "maximum": 10}
                    },
                    "required": ["question"]
                }
            }
        }
    ]


def _system_prompt() -> str:
    return (
        "You are a helpful AI assistant. You have access to two tools: "
        "(1) query_pdf(question, top_k) to search the provided HCIP PDF, and "
        "(2) search_web(query, num_results, region) for up-to-date info. "
        "Decide when to call tools. Prefer the PDF for questions directly related to the training material. "
        "Use web search for current events or when the PDF lacks the needed info. "
        "When you use tools, synthesize a concise answer with citations as [PDF chunk <id>] or URLs."
    )


def _call_tool(name: str, arguments_json: str) -> str:
    args = json.loads(arguments_json or "{}")
    if name == "search_web":
        results = search_web(
            query=args.get("query", ""),
            num_results=int(args.get("num_results" or 5)),
            region=args.get("region", "us-en"),
        )
        return json.dumps({"results": results})
    if name == "query_pdf":
        question = args.get("question", "")
        top_k = int(args.get("top_k") or 5)
        context = build_context_snippet(question=question, top_k=top_k)
        return json.dumps({"context": context})
    return json.dumps({"error": f"Unknown tool {name}"})


def chat_with_tools(question: str, temperature: Optional[float] = 0.2) -> str:
    client = _get_openai_client()
    model = _get_model()

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": question},
    ]

    tools = _tool_schemas()

    # Try Chat Completions with function-calling (most robust for tool loops)
    for _ in range(3):  # allow up to 3 tool iterations
        try:
            kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
            }
            if temperature is not None:
                kwargs["temperature"] = temperature
            resp = client.chat.completions.create(**kwargs)
        except BadRequestError as e:
            # Some models only support the default temperature; retry without it
            if "temperature" in str(e) and "default" in str(e):
                kwargs.pop("temperature", None)
                try:
                    resp = client.chat.completions.create(**kwargs)
                except Exception as e2:
                    return f"OpenAI API error: {e2}"
            else:
                return f"OpenAI API error: {e}"
        except Exception as e:
            # Final fallback: return error
            return f"OpenAI API error: {e}"

        msg = resp.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        if tool_calls:
            messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [tc.model_dump() for tc in tool_calls]})
            for tc in tool_calls:
                tool_name = tc.function.name
                tool_args = tc.function.arguments
                tool_output = _call_tool(tool_name, tool_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tool_name,
                    "content": tool_output,
                })
            # continue the loop for another model turn after tools
            continue
        else:
            return msg.content or ""

    return "Tool loop limit reached without final answer."


def direct_response_with_high_reasoning(prompt: str) -> Optional[str]:
    client = _get_openai_client()
    model = _get_model()

    # Attempt the Responses API with high reasoning effort
    try:
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": "You are a careful reasoner; think step by step and keep answers concise."},
                {"role": "user", "content": prompt},
            ],
            reasoning={"effort": "high"},
            max_output_tokens=800,
        )
        # The Python SDK typically provides output_text for convenience
        output_text = getattr(resp, "output_text", None)
        if output_text:
            return output_text
        # Fallback: try to access content
        if hasattr(resp, "output") and isinstance(resp.output, list) and resp.output:
            # Join any text segments
            texts = []
            for item in resp.output:
                if isinstance(item, dict):
                    if item.get("type") == "output_text" and "text" in item:
                        texts.append(item["text"])  # type: ignore[index]
            if texts:
                return "\n".join(texts)
        return None
    except Exception:
        return None