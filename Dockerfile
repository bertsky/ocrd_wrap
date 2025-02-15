ARG DOCKER_BASE_IMAGE
FROM $DOCKER_BASE_IMAGE
ARG VCS_REF
ARG BUILD_DATE
LABEL \
    maintainer="https://ocr-d.de/kontakt" \
    org.label-schema.vcs-ref=$VCS_REF \
    org.label-schema.vcs-url="https://github.com/bertsky/ocrd_wrap" \
    org.label-schema.build-date=$BUILD_DATE

WORKDIR /build/ocrd_wrap
COPY setup.py .
COPY ocrd_wrap/ocrd-tool.json .
COPY ocrd_wrap ./ocrd_wrap
COPY requirements.txt .
COPY README.md .
COPY Makefile .
RUN make install
RUN rm -rf /build/ocrd_wrap

WORKDIR /data
VOLUME ["/data"]
