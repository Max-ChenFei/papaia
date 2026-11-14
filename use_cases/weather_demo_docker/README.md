# Weather agent on two simulated machines (Docker, no GPU needed)

A LangChain agent with two tools:

- `get_weather(city)` is declared with `@required_fn(accel="A100:1", pip_install=["requests"])`.
  The GPU need is only declared; no GPU is used. The tool calls the free Open-Meteo API, which needs no API key.
- `current_utc_time()` has no declarations and runs in the agent process.

Docker Compose starts:
- `agent`: runs `papaia run`.
- `gpu-node`: a plain SSH + Python container that *declares* 2 GPUs.
- An Ollama server with `qwen3:0.6b` (CPU only; no API key).

The agent program is identical in both variants below. Only the compute-resource declaration (the node file) changes.

| Variant | Node file | Where `get_weather` runs |
|---|---|---|
| Remote (default) | `exec_nodes_remote.toml`: the agent machine has no GPU; `gpu-node` declares 2 | on `gpu-node`, via SSH (service on loopback, reached through an SSH tunnel) |
| Local | `exec_nodes_local.toml`: the agent machine declares 2 GPUs | on the agent machine, in its own virtual environment |

```bash
cd use_cases/weather_demo_docker
docker compose run --rm agent                                   # remote variant
NODES=exec_nodes_local.toml docker compose run --rm agent       # local variant
docker compose down                                             # stop the helper containers
```

The first run downloads the Ollama image and model (about 2 GB).
Each tool result shows the host it ran on, for example
`[tool get_weather] Berlin: 5.3 C, wind 9.8 km/h (tool ran on host 'gpu-node')`.
