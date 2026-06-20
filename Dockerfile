# PB2 dedicated server + tools to render config.yaml into pball/configs/
FROM nukla/paintball2:latest

USER root
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3 \
        python3-yaml \
    && rm -rf /var/lib/apt/lists/*

USER dpserver
COPY --chmod=755 scripts/render_config.py /scripts/render_config.py
COPY --chmod=755 scripts/config_maps.py /scripts/config_maps.py
COPY --chmod=755 scripts/list_bsp_textures.py /scripts/list_bsp_textures.py
COPY --chmod=755 scripts/apply-config.sh /scripts/apply-config.sh
COPY --chmod=755 scripts/start_dedicated.sh /scripts/start_dedicated.sh

WORKDIR /paintball2
