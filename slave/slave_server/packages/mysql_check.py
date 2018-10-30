from django.db import connection


def connection_usable():
    try:
        connection.connection.ping()
    except Exception as e:
        connection.close()

