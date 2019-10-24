FROM python:3.7.0a2-alpine3.6
RUN pip3 install --upgrade awscli
RUN apk --no-cache add curl 
COPY run-job.py /tmp
CMD python /tmp/run-job.py
