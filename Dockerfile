FROM ghcr.io/ad-sdl/madsci

LABEL org.opencontainers.image.source=https://github.com/AD-SDL/hudson_platecrane_module
LABEL org.opencontainers.image.description="Drivers and REST API's for the Hudson Platecrane robotic arm"
LABEL org.opencontainers.image.licenses=MIT

#########################################
# Module specific logic goes below here #
#########################################

RUN mkdir -p hudson_platecrane_module

COPY ./src hudson_platecrane_module/src
COPY ./README.md hudson_platecrane_module/README.md
COPY ./pyproject.toml hudson_platecrane_module/pyproject.toml
COPY ./tests hudson_platecrane_module/tests

RUN --mount=type=cache,target=/root/.cache \
    pip install -e ./hudson_platecrane_module

RUN usermod -aG dialout madsci

CMD ["python", "-m", "hudson_platecrane_module.platecrane_rest_node"]
#########################################
