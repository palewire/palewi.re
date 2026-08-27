---
title: 'Django recipe: Base management command for running custom SQL'
slug: django-recipe-base-management-command-running-custom-sql
published_at: '2014-07-25T12:02:15-07:00'
---
<p>Here is a simple <a href="https://docs.djangoproject.com/en/dev/howto/custom-management-commands/">Django management command</a> I use when I want to quickly execute custom SQL in the database.</p>

<p>For me, it comes in handy in cases working with large data sets where <a href="https://docs.djangoproject.com/en/dev/topics/db/queries/">Django's tools for interacting with the database</a> can take more time to craft and execute than a well-tailored <code><a href="http://www.w3schools.com/sql/sql_insert.asp">INSERT</a></code> command.</p>

<p>Here's the command. Paste it wherever you'd like in your project.</p>

<pre lang="python">from django.db import transaction, connection
from django.core.management.base import BaseCommand, CommandError


class SimpleSQLCommand(BaseCommand):
    help = "A base class for packaging simple SQL operations as a command"
    # Overriding these attributes is what you will need to do when subclassing
    # this command for use.
    flush = None  # An optional Django database model to be flushed
    sql = ""  # The SQL command to be run

    def handle(self, *args, **options):
        # Validate
        if not self.sql:
            raise CommandError("'sql' attribute must be set")

        # Flush model if it is provided
        if self.flush:
            if options.get("verbosity") >= 1:
                self.stdout.write("- Flushing %s" % self.flush.__name__)
            self.flush_model(self.flush)

        # Run custom sql
        if options.get("verbosity") >= 1:
            self.stdout.write("- Running custom SQL")
        self.execute_sql(self.sql)

    @transaction.atomic
    def flush_model(self, model):
        """
        Flushes the provided model using the lower-level TRUNCATE SQL command.
        """
        cursor = connection.cursor()
        cursor.execute("TRUNCATE %s CASCADE;" % (model._meta.db_table))

    @transaction.atomic
    def execute_sql(self, sql):
        """
        Executes the provided SQL command.
        """
        cursor = connection.cursor()
        cursor.execute(sql)</pre>

<p>Then simply import it into wherever you're putting your new custom command and provide the <code>sql</code> attribute. If you want to flush a model prior to running the command, as I often do, you can also provide it to the optional <code>model</code> attribute.</p>

<pre lang="python">from myapp import models
from mytoolbox import SimpleSQLCommand


class Command(SimpleSQLCommand):
    flush = models.MyModel
    # I might typically have more JOINs and other SQL crap going on
    # but let's keep it simple for this example
    sql = """
        INSERT INTO myapp_mymodel ("group","count")
        SELECT group, COUNT(*)
        FROM myapp_myothermodel
        GROUP BY group
        """</pre>

<p>Then, provided you've put your new command <a href="https://docs.djangoproject.com/en/dev/howto/custom-management-commands/#module-django.core.management">in the right spot</a>, running it should be as simple as this.</p>

<pre lang="bash">$ python manage.py mynewcommand</pre>