FROM python:3.6-alpine
COPY entrypoint.sh /opt/
COPY cloud_test_app /opt/cloud_test_app
COPY etc/conf.py /etc/cloud_test/
RUN apk add --no-cache \
      bash \
      gcc \
      curl \
      g++ \
      libstdc++ \
      linux-headers \
      musl-dev \
      postgresql-dev \
      mariadb-dev;

# TODO: install django app requirements and gunicorn

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r /opt/cloud_test_app/requirements.txt
RUN pip install --trusted-host pypi.python.org gunicorn

EXPOSE 8000
WORKDIR /opt

# TODO: set entrypoint and command (see entrypoint.sh)
ENTRYPOINT ["/opt/entrypoint.sh"]
CMD ["--start-service"]