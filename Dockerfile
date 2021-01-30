# This line links GHCR.io with the repository.
LABEL org.opencontainers.image.source=https://github.com/ussjoin/carmille

FROM alpine:latest

RUN apk update

RUN apk upgrade

RUN apk add --no-cache supervisor py3-pip python3-dev gcc musl-dev git

WORKDIR /root
RUN mkdir src

WORKDIR /root/src
COPY . /root/src/

RUN pip3 install -r requirements.txt

COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

EXPOSE 8000
