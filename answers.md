## Answers

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

## Closing Remarks / Reflection and Self Analysis

** Results View **
Initially I attempted to get the results in in the desired format by leveraging SQL's GROUP and COUNT functionality. While the code is now commented out I have left it in for reference only - under normal circumstances would remove it to both avoid shipping dead code and for better readability.

```
    # results = FilledQuestionnaire.objects.values("favourite_day") \
    #     .annotate(Count('favourite_day')) \
    #     .order_by('favourite_day') 
    
    # day_results = []
    # for result in results:
    #     day_results.append({
    #         "name": calendar.day_name[result["favourite_day"]],
    #         "count": result["favourite_day__count"],
    #         "percent": result["favourite_day__count"] / total * 100,
    #     })
```

There were a couple of reasons I didn't go with this method in the end.

* I still had to iterate over the results to calculate the percentages. I think its possible to get the percentages with some SQL magic - some subqueries and more good SQL stuff looking at some results on stack overflow. I didn't go down this path as the time investment to formulate the correct SQL and furthermore figure out this operation via the Django ORM.
* I breifly considered using the `raw` interface to run SQL directly instead of interfacing with the ORM but decided strongly against it for maintainability and portability reasons (ie, migrating the underlying database from SQLite3 to PostgreSQL, MySQL or something more production-worthy)
* I was querying the db multiple times for what was essentially different views of the same results - for the month results, for the day results and for the Days by Month results.

I decided the simplest way was to get the full results set and do some calculations in the results view - at least to get an MVP up and running. There may be a trade off with computation / memory usage for large datasets by storing them in memory and iterating over them.

At some point, I refactored how / where I was getting the total number of FilledQuestionnaires; Getting the total count upfront. 

```
results = FilledQuestionnaire.objects.all()
total = results.count()
```

After making this refactor I think it would be possible to do all of the calculations and formatting for the results in a single iteration of the list. I haven't decided if this is any better - might be worse for readability and im not sure how large the computation / memory gains would be in practice. This would be something to explore later.

**Docker file**

`# TODO: install django app requirements and gunicorn`

I interpretted the TODO note (`# TODO: install django app requirements and gunicorn`) very literally - installing requirements from `requirements.txt` and installing gunicorn in two seperate operations. 

```
RUN pip install --trusted-host pypi.python.org -r /opt/cloud_test_app/requirements.txt
RUN pip install --trusted-host pypi.python.org gunicorn
```

It works but, unless there is a specific reason to keep the installation of gunicorn seperate from the rest of the requirements I would probably list gunicorn in `requirements.txt` and allow it to be installed along with all of the other packages.