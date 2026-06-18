> See [`../ReadMe.md`](../ReadMe.md) for prerequisites and environment setup.

# ray_serve

## Install Ray and start the Ray head
```bash
python -m pip install -U "ray[serve]"
ray start --head
```

## Run the server
```bash
scp -r grounding user@172.30.162.209:~/ # copy the grounding folder to the remote node
ssh user@172.30.162.209 # SSH login
cd ~/grounding # including main.py and requirements.txt
python3 -m venv .venv # create a Python environment
source .venv/bin/activate
python -m pip install -r requirements.txt # install dependencies
serve start --http-host 0.0.0.0 --http-port 43141 && serve run ray_serve:deployment # run the service
```

## Run the agent
```bash
uv run --group genartist python agent.py
```
