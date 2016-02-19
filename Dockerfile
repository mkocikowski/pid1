FROM ubuntu:15.10
RUN apt-get update && apt-get install -y vim python
RUN useradd --home-dir=/opt/orphanmaker --create-home orphanmaker
USER orphanmaker
ENTRYPOINT ["/usr/bin/python"]

