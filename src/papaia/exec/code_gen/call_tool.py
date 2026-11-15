"""Agent-side call of an out-of-process tool, used by the generated stubs.

Every failure is raised as a ``ToolError`` that names the tool and says what
went wrong, so the user knows where the tool stopped working.
"""

import requests


class ToolError(RuntimeError):
    """An out-of-process tool failed or could not be called."""


def call_tool(tool: str, url: str, payload: dict):
    try:
        response = requests.post(url, json=payload)
    except (TypeError, ValueError) as e:  # json encoding (requests wraps ValueError)
        raise ToolError(
            f"Tool '{tool}': arguments must be JSON-serializable ({e})"
        ) from None
    except requests.ConnectionError as e:
        raise ToolError(
            f"Tool '{tool}': its service at {url} is not reachable ({e})"
        ) from None

    if response.status_code == 200:
        return response.json()["result"]

    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    if response.status_code == 422:
        if isinstance(detail, list):  # pydantic validation errors
            detail = "; ".join(
                f"{'.'.join(str(x) for x in d.get('loc', [])[1:])}: {d.get('msg')}"
                for d in detail
            )
        raise ToolError(f"Tool '{tool}': invalid arguments ({detail})")
    if isinstance(detail, dict) and "error" in detail:
        raise ToolError(
            f"Tool '{tool}' failed in its service: {detail['error']}\n\n"
            f"Traceback in the tool's service:\n{detail.get('traceback', '')}"
        )
    raise ToolError(f"Tool '{tool}' failed in its service: {detail}")
