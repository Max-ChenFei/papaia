# Terminal Commands for Running the Agent
## Run the server
```bash
scp -r grounding user@172.30.162.209:~/ # copy the grounding folder to the remote node
ssh user@172.30.162.209 # SSH login
cd ~/grounding # including main.py and requirements.txt
python3 -m venv .venv # create a Python environment
source .venv/bin/activate
python -m pip install -r requirements.txt # install dependencies
fastmcp run server.py:mcp --transport http --port 52273 # run the service

```

## Run the agent
```bash
python path/to/agent.py
```