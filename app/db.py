import sqlite3
from datetime import datetime

import click
from flask import current_app, g

# g is a special object that's unique for each request
# it stores the current connection we have to the database

def get_db():
    if 'db' not in g:
        # establishes connection to our database file
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # tells connection to return rows that behave like dicts
        g.db.row_factory = sqlite3.Row

    return g.db

# checks if connection was created. if so, we close it.
def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

# run sql commands in schema.sql to the db.py file
def init_db():
    # get database connection
    db = get_db()

    # run commands read from file (create tables in db)
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

# defines a command line command
@click.command('init-db')
def init_db_command():
    """ Clear existing data and create new tables"""
    # calls function we created above
    init_db()
    # show a success message to the user
    click.echo('Initialized the database')

# register these functions with our app as the argument
def init_app(app):
    # call close_db when cleaning up after returning the response
    app.teardown_appcontext(close_db)
    # creates a new command that can be called next to the flask command
    app.cli.add_command(init_db_command)