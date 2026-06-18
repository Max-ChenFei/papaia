> See [`../ReadMe.md`](../ReadMe.md) for prerequisites and environment setup.

# papaia

### Additional prerequisites for remote VM deployment
1. Start an SSH server (e.g., `openssh-server`) on the remote VM.
2. Install Python virtual environment support (e.g., `python3-venv`) on the remote VM.

## Step 1: Configure available node

Declare the nodes available for tool placement. Each node specifies its location, resources, and optional SSH credentials for remote nodes.


**for example** (`exec_nodes_remote.toml` in the current directory):
```toml
[nodes.local]
location = "local"
cpus = 8
memory = 32


[nodes.vm2]
location = "remote"
cpus = 8
memory = 48
accel = "RTX 4090:1"
host = "c8891fda-f917-48e0-96b0-9d8d60bbccb2.tenants.hivecompute.ai"
port = 32377
username = "ubuntu"
```

## Step 2: Annotate tool requirements in `agent.py`

Decorate each tool class with `@required_cls` to declare its execution requirements. Papaia uses these to match the tool to a suitable node and provision its virtual environment automatically.

```python
@required_cls(
    entry="forward",        # method papaia wraps as the remote entry point
    accel="RTX 8000",       # GPU requirement used to select a matching node
    pip_install=[           # packages installed in the tool's isolated venv
        "torch --index-url https://download.pytorch.org/whl/cu124",
        "git+https://github.com/Max-ChenFei/papaia.git",
        "transformers",
        "diffusers",
        "Pillow",
        "requests",
    ],
)
class Text2Image(Tool):
    ...
```

## Step 3: Run the agent
```bash
uv run --group genartist 
papaia run agent.py -c exec_nodes_remote.toml
```
