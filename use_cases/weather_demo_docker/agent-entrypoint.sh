#!/bin/sh
set -e
# Create an SSH key shared with gpu-node (via the `keys` volume).
mkdir -p /root/.ssh
[ -f /keys/id_ed25519 ] || ssh-keygen -q -t ed25519 -N '' -f /keys/id_ed25519
cp /keys/id_ed25519 /keys/id_ed25519.pub /root/.ssh/
# Wait for gpu-node's SSH server and trust its host key.
until nc -z gpu-node 22; do sleep 1; done
ssh-keyscan -q gpu-node > /root/.ssh/known_hosts 2>/dev/null
exec "$@"
