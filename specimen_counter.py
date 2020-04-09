import psycopg2
import numpy as np
import pandas as pd


def connect(db_params):
    """Connect to PostgreSQL database.

    Parameters
    ----------
    db_params : str
        Database connection parameters.

    Returns
    -------
    Connection
        Database connection object.
    """
    try:
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect("dbname='{}'".format(db_params))

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    return conn

def count_specimen(conn):
    """Retrieve and update all new entries in qpcr_records_test_results table.

    Parameters
    ----------
    conn : Connection
        psycopg2.Connection object
    """
    cur = conn.cursor()

    # Note: The command to obtain all of the tables within the SQLite database is
    #       'SELECT name from sqlite_master where type= "table"' (in case we need it)

    # * Retrieve new entries
    # Read in last read timestamp file
    # Example for counting number of samples that are processsed to this step
    cur.execute(f'SELECT COUNT(plate_name) \
                  FROM qpcr_results \
                  WHERE plate_name != {default_value}')
    result = cur.fetchone()['count']

    dict_ = {'Step 1' : result}

    return dict_



def main():
    # Specify the database file name and generate the database connection
    print(f"{datetime.now().strftime('%m/%d/%Y, %H:%M:%S')} | Accessing database ...")
    # NOTE: change database name and add authentication flags
    database = r"db.sqlite3"
    conn = connect(database)
    process_new_entries(conn)

if __name__ == '__main__':
    main()
