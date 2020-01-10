FROM python:3

LABEL maintainer="Gabe Weiss <gweiss@google.com>"

RUN pip install -r ./requirements.txt

ENV DB_USER "<db user name>"
ENV DB_PASS "<db user password>"
ENV DB_NAME "<database name for fake data>"

# Note that SQL_HOST is not needed IF you're connecting to
# a localhost db or Cloud SQL Proxy AND you're not using Docker on MacOS
# Docker on MacOS uses hypervisor and doesn't share network with
# the host machine even when you set -net=host
# Uncomment SQL_HOST line and specify the IP to connect to

#ENV SQL_HOST "<IP address of Cloud SQL instance to connect to>"

CMD [ "python", "./mysql_faker.py" ]

