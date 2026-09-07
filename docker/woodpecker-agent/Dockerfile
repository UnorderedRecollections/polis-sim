# Woodpecker agent — executes pipeline steps as sibling containers via the
# podman socket. On podman-machine (macOS) it MUST run with:
#   --user 0:0 --security-opt label=disable
#   -v /run/user/501/podman/podman.sock:/var/run/docker.sock
# (see docs/services/woodpecker.md for the reasons).
FROM woodpeckerci/woodpecker-agent:v3
CMD ["agent"]
