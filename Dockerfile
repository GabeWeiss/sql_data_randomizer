FROM python:3

LABEL maintainer="Gabe Weiss"

COPY ./requirements.txt /app/
COPY ./mysql_faker.py /app/

WORKDIR /app

RUN pip install -r requirements.txt

ENV DB_USER "<user>"
ENV DB_PASS "<password>"
ENV DB_NAME "<db name>"

# Note that SQL_HOST is not needed IF you're connecting to
# a localhost db or Cloud SQL Proxy AND you're not using Docker on MacOS
# Docker on MacOS uses hypervisor and doesn't share network with
# the host machine even when you set -net=host

# Uncomment SQL_HOST line and specify the IP to connect to
#ENV SQL_HOST "<database IP>"

# passing the --auto flag to remove interactivity from the script
CMD [ "python", "mysql_faker.py", "--auto", "-l 10", "-e 100", "-c" ]

