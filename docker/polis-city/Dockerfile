# polis-city — a city node: one container per city of the federation.
# Contains the polis package and git; the city's slice is mounted at
# /etc/polis/city.json (POLIS_CITY_CONFIG), which puts the chamber in
# container mode. Federal credentials are never present here.
FROM python:3.12-alpine

RUN apk add --no-cache git

WORKDIR /opt/polis
COPY pyproject.toml ./
COPY polis ./polis
RUN pip install --no-cache-dir .

# idle node: driven via `podman exec <container> polis …`
CMD ["sleep", "infinity"]
