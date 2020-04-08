import psycopg2
from datetime import datetime
import pytz

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
        conn = psycopg2.connect(db_params)

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    return conn

def process_new_entries(conn):
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
    with f as open('time_retrieved.txt', 'r'):
        last_retrieved_time = f.read()

    # Get current timestamp
    current_time = datetime.now(pytz.timezone('America/Los_Angeles'))

    # Query for new entries
    cur.execute(f'SELECT * FROM qpcr_results \
                  WHERE timestamp_field > {last_retrieved_time} \
                  AND timestamp_field <= {current_time}')

    # * Process raw data (Ct values, decision tree)
    for row in cur.fetchall():
        print(row)
        # TODO

    # * Update entries in database

    # * Export entries to csv + SFTP to Rady site

    # Save last read timestamp to file
    with f as open('time_retrieved.txt', "w"):
        f.write(current_time)

    cur.close()
    print('Database connection closed.')

def main():
    # Specify the database file name and generate the database connection
    print(f"{datetime.now().strftime('%m/%d/%Y, %H:%M:%S')} | Accessing database ...")
    database = r"db.sqlite3"
    conn = connect(database)
    process_new_entries(conn)

if __name__ == '__main__':
    main()
