# Stage: s6-overlay-base
# Purpose: Installs s6-overlay and rootfs
# Comments:
#  - Don't leave anything extra in here either
FROM ghcr.io/astral-sh/uv:0.7.3-python3.11-alpine AS s6-overlay-base

WORKDIR /usr/src/s6

# https://github.com/just-containers/s6-overlay#customizing-s6-overlay-behaviour
ENV \
    S6_BEHAVIOUR_IF_STAGE2_FAILS=2 \
    S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0 \
    S6_VERBOSITY=1 \
    PATH=/command:$PATH

# Buildx provided, must be defined to use though
ARG TARGETARCH
ARG TARGETVARIANT
# Lock this version
ARG S6_OVERLAY_VERSION=3.2.1.0

ARG S6_BUILD_TIME_PKGS="curl \
                        xz"

RUN set -eux \
    && echo "Installing build time packages" \
      && apk add --no-cache --virtual .s6-utils ${S6_BUILD_TIME_PKGS} \
    && echo "Determining arch" \
      && S6_ARCH="" \
      && if [ "${TARGETARCH}${TARGETVARIANT}" = "amd64" ]; then S6_ARCH="x86_64"; \
      elif [ "${TARGETARCH}${TARGETVARIANT}" = "arm64" ]; then S6_ARCH="aarch64"; fi\
      && if [ -z "${S6_ARCH}" ]; then { echo "Error: Not able to determine arch"; exit 1; }; fi \
    && echo "Installing s6-overlay for ${S6_ARCH}" \
      && curl --fail --silent --no-progress-meter --show-error --location --remote-name-all --parallel --parallel-max 4 \
        "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" \
        "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz.sha256" \
        "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz" \
        "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz.sha256" \
      && echo "Validating s6-archive checksums" \
        && sha256sum -c ./*.sha256 \
      && echo "Unpacking archives" \
        && tar --directory / -Jxpf s6-overlay-noarch.tar.xz \
        && tar --directory / -Jxpf s6-overlay-${S6_ARCH}.tar.xz \
      && echo "Removing downloaded archives" \
        && rm ./*.tar.xz \
        && rm ./*.sha256 \
    && echo "Cleaning up image" \
      && apk del --no-cache .s6-utils

# Copy our service defs and filesystem
COPY ./docker/rootfs/ /

# Stage: main-app
# Purpose: The final image
# Comments:
#  - Don't leave anything extra in here
FROM s6-overlay-base AS main-app

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # https://docs.astral.sh/uv/reference/settings/#link-mode
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/cache/uv/

# Set the working directory inside the container
WORKDIR /app

COPY --chown=1000:1000 ["pyproject.toml", "uv.lock", "manage.py", "/app/"]

# hadolint ignore=DL3042
RUN --mount=type=cache,target=${UV_CACHE_DIR},id=python-cache \
  set -eux \
  && echo "Installing system packages" \
    && apk add --no-cache nginx postgresql-client \
  && echo "Installing build system packages" \
    && apk add --no-cache --virtual .python-build \
        postgresql-dev \
        mariadb-dev \
        pkgconfig \
  && echo "Installing Python requirements" \
    && uv export --quiet --no-dev --all-extras --format requirements-txt --output-file requirements.txt \
    && uv pip install --system --no-python-downloads --python-preference system --requirements requirements.txt \
  && echo "Cleaning up image" \
    && apk del --no-cache .python-build

COPY --chown=1000:1000 ["./memoria/",  "/app/memoria/"]

RUN set -eux \
  && sed -i '1s|^#!/usr/bin/env python3|#!/command/with-contenv python3|' manage.py \
  && echo "Setting up user/group" \
    && addgroup -S -g 1000 memoria \
    && adduser -S -u 1000 -G memoria memoria \
  && echo "Creating volume directories" \
    && mkdir --parents --verbose /app/data/ \
    && mkdir --parents --verbose /app/data/logs/ \
    && mkdir --parents --verbose /app/data/logs/nginx/ \
    && mkdir --parents --verbose /app/data/nginx/ \
    && mkdir --parents --verbose /app/static/ \
    && mkdir --parents --verbose /app/media/ \
    && chown --changes --recursive memoria:memoria /app/ \
  && echo "Collecting static files" \
    && s6-setuidgid memoria python3 manage.py collectstatic --clear --no-input --link \
  && echo "Adjusting all permissions" \
    && chown --changes --recursive memoria:memoria /app/


EXPOSE 8101

ENTRYPOINT ["/init"]
