FROM ghcr.io/ad-sdl/wei:v0.5.8

LABEL org.opencontainers.image.source=https://github.com/AD-SDL/hudson_platecrane_module
LABEL org.opencontainers.image.description="Drivers and REST API's for the Hudson Platecrane and Sciclops robots"
LABEL org.opencontainers.image.licenses=MIT

#########################################
# Module specific logic goes below here #
#########################################

RUN apt update && apt install -y libusb-1.0-0-dev && rm -rf /var/lib/apt/lists/*

RUN mkdir -p hudson_platecrane_module

COPY ./src hudson_platecrane_module/src
COPY ./README.md hudson_platecrane_module/README.md
COPY ./pyproject.toml hudson_platecrane_module/pyproject.toml
COPY ./tests hudson_platecrane_module/tests

RUN --mount=type=cache,target=/root/.cache \
    pip install -e ./hudson_platecrane_module

RUN usermod -aG dialout app

CMD ["python", "-,", "sciclops_rest_node"]
#########################################
