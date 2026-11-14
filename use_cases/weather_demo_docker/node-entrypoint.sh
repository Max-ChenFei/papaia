#!/bin/sh
set -e
until [ -f /keys/id_ed25519.pub ]; do sleep 1; done
install -d -m 700 -o papaia -g papaia /home/papaia/.ssh
install -m 600 -o papaia -g papaia /keys/id_ed25519.pub /home/papaia/.ssh/authorized_keys
ssh-keygen -A
exec /usr/sbin/sshd -D -e
