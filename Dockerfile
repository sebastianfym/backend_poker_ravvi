FROM ubuntu:22.04

#ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN apt update
RUN apt upgrade -y
RUN apt install -y mc postgresql-client python3 python3-pip

RUN groupadd --gid 2002 poker
RUN useradd --create-home --shell /bin/bash --uid 2002 --gid 2002 poker

USER poker
WORKDIR /home/poker

# create directories with poker owner
RUN mkdir -p /home/poker/bin
RUN mkdir -p /home/poker/.local/bin
RUN mkdir -p /home/poker/.cache
RUN mkdir -p /home/poker/.cache/pip
RUN mkdir -p /home/poker/dist
RUN mkdir -p /home/poker/log

COPY --chown=poker:poker dist dist
RUN pip3 install --user -f dist ravvi-poker

ENTRYPOINT [ "/bin/bash", "-l", "-c"]
CMD [ "env" ]

