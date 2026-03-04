# Terminal Commands for Running the Agent
## Run the server
```bash
scp -r grounding user@172.30.162.209:~/ # copy the grounding folder to the remote node
ssh user@172.30.162.209 # SSH login
cd ~/grounding # including main.py and requirements.txt
python3 -m venv .venv # create a Python environment
source .venv/bin/activate
python -m pip install -r requirements.txt # install dependencies
serve start --http-host 0.0.0.0 --http-port 52273 && serve run ray_serve:deployment # run the service

```

## Run the agent
```bash
python path/to/agent.py
```