# A Papaia tool in Google ADK (no GPU, no API key)

`factor` is declared with `@required_fn(pip_install=["sympy"])`, so Papaia runs it in its own virtual environment, and ADK sees only the generated stub.
The script registers the tool with an ADK `Agent`, prints the declaration ADK builds for the LLM (the same as for the undecorated function), and calls the tool through ADK's `FunctionTool`.

```bash
cd use_cases/adk_function_tool
uv run --project ../.. --with "google-adk==2.14.1" papaia run agent.py -c exec_nodes.toml
```

Expected output (after the server logs):
```
Declaration: description='Factor a polynomial expression. ...' name='factor' ... parameters_json_schema={'properties': {'expression': {'title': 'Expression', 'type': 'string'}}, 'required': ['expression'], ...}
Result: (x - 1)*(x + 1)
```
