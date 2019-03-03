#Answers

**Explain how the config for this app works, and why when using docker compose might this be a good way to configure rather than a config file**

Django configuration is loaded from 
`opt/cloud_test_app/cloud_test/settings/config.py` though this config file does little more than read values from environment variables - in some case providing default values if no such environment variabe is found - and populating them into module level variables.

A second config file exists,
`/opt/cloud_test_app/cloud_test/settings/local.py`, which override config.py

This allows us to set fixed/stored config values that extend the config.py values and also allows us to make configuration changes in our dev environment without having to set environment variables there.

Docker compose allows us to specify environment variables via the `environment` property of the service configuration in our `docker-compose.yml` file. Django would then be able to access these values as environment variables at runtime.

**Explain why the startup_check.py file exists and what it does**

>To facilitate easier upgrades and container rollovers we wanted each container to be safe to start up on it's own, and attempt to handle new migrations (if needed) and collection of static files.
>
>This is run on every container start up and simply ensures that the database is in the state the container needs it to be to run.

1. Sets runtime parameters from environment variables
2. Checks if there are any migrations which need to be run and runs migrations
3. Checks if the app has a superuser and if not creates a default superuser
4. Runs collectstatic collect static files from each of your applications into a single location that can easily be served in production.

**Explain what the entrypoint.sh file does**

Starts gunicorn and also acts as an interface to manage the django app via manage.py. The devloper can pass 

`--django-manage` forwards cli arguments following --django-manage to manage.py

`--manage-shell` gets a django shell - though, this didn't work for me

`--start-service` starts the service (running startup_checks.py) and start gunicorn

`--hot-reload` similar to --start-service but calls gunicorn with `--reload` flag. Good for development

While the first two options executre commands with manage.py the second to options simply set flags to contol how gunicorn is started further below.

The configuration in the dockerfile means that starting docker without passing any commands of the above commands will run with the `--start-service`

```
# TODO: set entrypoint and command (see entrypoint.sh)
ENTRYPOINT ["/opt/entrypoint.sh"]
CMD ["--start-service"]
```