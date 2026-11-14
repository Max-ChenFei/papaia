> See [`../ReadMe.md`](../ReadMe.md) for prerequisites and environment setup.

# baseline

## Run the server
```bash
scp server.py user@172.30.162.209:~/ # copy the server file to the remote node
ssh user@172.30.162.209 # SSH login
python3 -m venv .venv # create a Python environment
source .venv/bin/activate
python -m pip install "transformers<5" torch Pillow requests fastapi uvicorn # install dependencies
uvicorn server:app --port 52273 # run the service
```

## Run the agent
```bash
ssh -f -N -L 52273:localhost:52273 user@172.30.162.209 # forward the service port to this machine
uv run --group cigeva python agent.py
```