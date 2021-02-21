FROM ubuntu:18.04
MAINTAINER Julian von Mendel "prog@derjulian.net"
EXPOSE 8080
COPY . /app
RUN apt update
RUN apt install -y build-essential
RUN apt install -y python3 python3-pip
WORKDIR /app
RUN make install
RUN make train
RUN make test
ENTRYPOINT ["make"]
CMD ["help"]
