# polis-city — a city node: one container per city of the federation.
# Also the image the Mechanical Magistrate's pipeline steps run in (task
# 0041): it carries the polis package, git, and the legal-design data the
# CLI's ontology loaders read (POLIS_DATA_DIR). Contains no credentials;
# the city's slice is mounted at /etc/polis/city.json (POLIS_CITY_CONFIG),
# which puts the chamber in container mode. Federal credentials are never
# present here.
FROM python:3.12-alpine

RUN apk add --no-cache git

WORKDIR /opt/polis
COPY pyproject.toml ./
COPY polis ./polis
RUN pip install --no-cache-dir .

# the legal-design YAML (data/world/legal/) — ontology/norms loaders read
# it at import; POLIS_DATA_DIR points the runtime at this copy
COPY data/world/legal ./data/world/legal
ENV POLIS_DATA_DIR=/opt/polis/data

# idle node: driven via `podman exec <container> polis …`
CMD ["sleep", "infinity"]
