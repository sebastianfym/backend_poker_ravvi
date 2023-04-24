FROM ubuntu:22.04

#ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN apt update
RUN apt upgrade -y
RUN apt install -y mc postgresql-client python3 python3-pip

RUN useradd --create-home --shell /bin/bash ravvi

USER ravvi
WORKDIR /home/ravvi

# create directories with ravvi owner
RUN mkdir -p /home/ravvi/bin
RUN mkdir -p /home/ravvi/.local/bin
RUN mkdir -p /home/ravvi/.cache
RUN mkdir -p /home/ravvi/.cache/pip
RUN mkdir -p /home/ravvi/dist

COPY --chown=ravvi:ravvi dist dist
RUN pip3 install --user -f dist ravvi-poker-backend

ENTRYPOINT [ "/bin/bash", "-l", "-c"]
CMD [ "env" ]

