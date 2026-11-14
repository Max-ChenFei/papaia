> See [`../ReadMe.md`](../ReadMe.md) for prerequisites and environment setup.

# ray_serve

## Run the server
```bash
scp server.py user@172.30.162.209:~/ # copy the server file to the remote node
ssh user@172.30.162.209 # SSH login
python3 -m venv .venv # create a Python environment
source .venv/bin/activate
python -m pip install "transformers<5" torch Pillow requests fastapi "ray[serve]" # install dependencies
ray start --head && serve start --http-host 0.0.0.0 --http-port 52273 && serve run server:deployment # run the service
```

## Run the agent
```bash
ssh -f -N -L 52273:localhost:52273 user@172.30.162.209 # forward the service port to this machine
uv run --group cigeva python agent.py
```