FROM python:3

WORKDIR /usr/src/app

RUN apt update && apt install -y git-lfs && apt clean && rm -rf /var/lib/apt/lists/* 

COPY . .

RUN python setup.py install

ENTRYPOINT [ "/usr/local/bin/outline-backup" ]
