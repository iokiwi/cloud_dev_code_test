import logging
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cloud_test.settings") # noqa
import django
django.setup() # noqa

from io import StringIO
from time import sleep

from django.core import management
from django.contrib.auth.models import User
from django.db.utils import OperationalError

# NOTE(adriant): This assumes our django app and environment has
# django-db-locking installed and setup in installed apps.
from locking.models import NonBlockingLock
from locking.exceptions import AlreadyLocked

from tenacity import (
    retry, stop_after_attempt, wait_fixed, retry_if_exception_type, after_log)

from cloud_test.utils import parse_boolean

# Lock expiry times
MIGRATION_LOCK_AGE = int(os.environ.get("MIGRATION_LOCK_AGE", 120))
STATIC_LOCK_AGE = int(os.environ.get("STATIC_LOCK_AGE", 240))


# For creating a default admin user
DEFAULT_ADMIN_USERNAME = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_EMAIL = os.environ.get(
    "DEFAULT_ADMIN_EMAIL", "admin@example.com")
DEFAULT_ADMIN_PASSWORD = os.environ.get("DEFAULT_ADMIN_PASSWORD", "adminpass")


logger = logging.getLogger('django')
logger.info("Django startup Checks")


@retry(retry=retry_if_exception_type(OperationalError),
       stop=stop_after_attempt(5), wait=wait_fixed(3),
       after=after_log(logger, logging.INFO))
def get_migration_data():
    logger.info("getting migration data")
    with StringIO() as migration_output:
        management.call_command(
            'showmigrations', '--plan', stdout=migration_output)

        migrations = migration_output.getvalue().splitlines()

        num_migrations = len(migrations)

        # TODO: Go through the migration lines.
        # If the migration is a needed migration, add it to: needed_migrations
        # If the migration is from the locking app, also add it to:
        #   locking_migrations

        needed_migrations = [m for m in migrations if "[ ]" in m ]
        locking_migrations = [m for m in migrations if "locking" in m ]
        num_needed_migrations = len(needed_migrations)

        return {
            'migrations': migrations,
            'num_migrations': num_migrations,

            # A set() with all the needed migration lines
            'needed_migrations': needed_migrations,
            # A set() with all the needed migration lines
            'locking_migrations': locking_migrations,
            # the number of needed migrations
            'num_needed_migrations': num_needed_migrations,
        }


@retry(retry=retry_if_exception_type(OperationalError),
       stop=stop_after_attempt(5), wait=wait_fixed(3),
       after=after_log(logger, logging.INFO))
def run_migrations():
    logger.info("running migrations")
    with StringIO() as migration_output:
        management.call_command(
            'migrate', '--noinput', stdout=migration_output)

        # Will only print if the above does not fail
        logger.info("\n" + migration_output.getvalue())


needs_migration = False
locking_migrated = False
initial_migration = False


logger.info("Checking for migrations")
migration_data = get_migration_data()

if migration_data['num_needed_migrations'] == migration_data['num_migrations']:
    logger.info("Initial migrations are needed")
    initial_migration = True
    needs_migration = True
elif migration_data['num_needed_migrations'] != 0:
    logger.info("There are migrations to apply")
    needs_migration = True

    if not (migration_data['needed_migrations']
            & migration_data['locking_migrations']):
        logger.info(
            "Locking database models have been migrated and can be used")
        locking_migrated = True
else:
    logger.info("There are no migrations to apply")


if needs_migration:
    logger.info("Applying migrations")

    if initial_migration or not locking_migrated:
        logger.info("Applying initial migrations")
        run_migrations()
    else:
        while(True):
            migration_data = get_migration_data()

            if migration_data['num_needed_migrations'] == 0:
                logger.info(
                    "Another process has completed the migrations, "
                    "moving on")
                break

            try:
                logger.info("Acquiring migration database lock")
                lock = NonBlockingLock.objects.acquire_lock(
                    lock_name='migrating_database', max_age=MIGRATION_LOCK_AGE)

                try:
                    logger.info("Applying needed migrations")
                    run_migrations()
                    break
                finally:
                    lock.release()
                    logger.info("Releasing migration database lock")
            except AlreadyLocked:
                logger.info(
                    "Another process already has the migration lock, waiting.")
                sleep(5)
                logger.info("Still waiting...")


@retry(retry=retry_if_exception_type(OperationalError),
       stop=stop_after_attempt(3), wait=wait_fixed(2),
       after=after_log(logger, logging.INFO))
def handle_super_users():
    super_users = User.objects.filter(is_superuser=True)

    if not super_users:
        logger.info("There are no super users.")
        logger.info("Creating default super user")
        User.objects.create_superuser(
            DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_EMAIL,
            DEFAULT_ADMIN_PASSWORD)
    else:
        logger.info("One or more superusers exist")


logger.info("Checking for superusers")
handle_super_users()


static_collect = parse_boolean(
    os.environ.get("DJANGO_AUTO_COLLECT_STATIC", True))

if static_collect:
    logger.info("Running static files collection")
    try:
        logger.info("Acquiring collectstatic lock")
        lock = NonBlockingLock.objects.acquire_lock(
            lock_name='collectstatic', max_age=STATIC_LOCK_AGE)
        try:
            with StringIO() as collectstatic_output:
                management.call_command(
                    'collectstatic', '--noinput', stdout=collectstatic_output)
                logger.info("\nCollect static output:\n")
                logger.info(collectstatic_output.getvalue())
        finally:
            lock.release()
            logger.info("Releasing collectstatic lock")
    except AlreadyLocked:
        logger.info("Another process already has the static lock, waiting...")
        while(True):
            try:
                lock = NonBlockingLock.objects.acquire_lock(
                    lock_name='collectstatic', max_age=STATIC_LOCK_AGE)
                lock.release()
                logger.info(
                    "Another process has finished collecting static files")
                break
            except AlreadyLocked:
                logger.info("Still waiting...")
            sleep(5)
else:
    logger.info("Skipping static files collection")

logger.info("Finished django startup Checks\n")
