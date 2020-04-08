import psycopg2
from datetime import datetime
import pytz
import numpy as np
import pandas as pd
import os
from results import Results

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
    # NOTE: make the time_retrieved, read_barcode files

    with f as open('time_retrieved.txt', 'r'):
        last_retrieved_time = f.read()

    # Clear previous files for transfer
    os.system('rm Result_transfer_*')

    # Get current timestamp
    current_time = datetime.now(pytz.timezone('America/Los_Angeles'))

    # Query for new entries
    cur.execute(f'SELECT * FROM qpcr_results \
                  WHERE sampling_date > {last_retrieved_time} \
                  AND sampling_date <= {current_time}')

    # * Process raw data (Ct values, decision tree)
    # Instatiate results class
    r = Results()
    # Tabulate the results
    # Processing excel files seperately from barcodes so that each file is parsed only once to reduce compute time
    raw_vals_dict = {}
    barcode_dict = {}
    files_to_parse = []
    for row in cur.fetchall():
        barcode_dict[row['barcode']] = {'file':row['pcr_results_csv'],'position':row['plate_6_well']}
        files_to_parse.append(row['pcr_results_csv'])
    files_to_parse = list(np.unique())
    for file in files_to_parse:
        raw_vals_dict[file] = r.get_results(file)
    # * Update entries in database
    # * Get fake names associated with barcodes
    # NOTE: double check barcode and fake name csv file name
    barc_df = pd.read_csv('barcodes.csv')
    barc_df = barc_df.set_index('barcode')
    for key,val in barcode_dict.items():
        # MS2 Ct
        cur.execute(f'UPDATE qpcr_results \
                    SET ms2_ct_value = {raw_vals_dict[val['file']][val['position']]['MS2']} \
                    WHERE barcode = {key})

        # N gene Ct
        cur.execute(f'UPDATE qpcr_results \
                    SET n_ct_value = {raw_vals_dict[val['file']][val['position']]['N gene']} \
                    WHERE barcode = {key})

        # ORF1ab Ct
        cur.execute(f'UPDATE qpcr_results \
                    SET orf1ab_ct_value = {raw_vals_dict[val['file']][val['position']]['ORF1ab']} \
                    WHERE barcode = {key})

        # S gene Ct
        cur.execute(f'UPDATE qpcr_results \
                    SET s_ct_value = {raw_vals_dict[val['file']][val['position']]['S gene']} \
                    WHERE barcode = {key})

        # Diagnosis
        cur.execute(f'UPDATE qpcr_results \
                    SET decision_tree_results = {raw_vals_dict[val['file']][val['position']]['diagnosis']} \
                    WHERE barcode = {key})

        # Fake name
        # NOTE: double check fake name columns
        cur.execute(f'UPDATE qpcr_results \
                    SET fake_name = {barc_df['first name'][key] + ' ' + barc_df['last name'][key]} \
                    WHERE barcode = {key})

    # * Now pull entries that have been cleared by technician for transfer
    # * but haven't been sent yet
    query = f'SELECT * FROM qpcr_results \
                  WHERE file_transfer_status = 'Not Complete' \
                  AND final_results != 'Undetermined''
    df = pd.read_sql_query(query,conn)
    keep_columns = []
    df = df.drop(df.columns.difference(keep_columns), 1, inplace=True)
    new_finished_barcodes = list(df['barcode'])
    # * Export entries to csv + SFTP to Rady site
    #temporarily save the csv file, sftp it then delete
    time_str = str(current_time.month) + str(current_time.day) + str(current_time.year) + '_' + str(current_time.hour) + str(current_time.minute)
    df.to_csv("Result_transfer_"+ time_str + '.csv')
    print("Sending data to Rady red cap server")
    # NOTE: make sure sftp password is in sftp_transfer.exp script
    os.system('expect sftp_transfer.exp Result_transfer_' + time_str + '.csv')
    # Save last read timestamp to file
    with f as open('time_retrieved.txt', "w"):
        f.write(current_time)
    # Update db file transfer statuses for files just transfered
    for barcode in new_finished_barcodes:
        cur.execute(f'UPDATE qpcr_results \
                    SET file_transfer_status = 'Complete' \
                    WHERE barcode = {barcode})




    cur.close()
    print('Database connection closed.')

def main():
    # Specify the database file name and generate the database connection
    print(f"{datetime.now().strftime('%m/%d/%Y, %H:%M:%S')} | Accessing database ...")
    # NOTE: change database name and add authentication flags
    database = r"db.sqlite3"
    conn = connect(database)
    process_new_entries(conn)

if __name__ == '__main__':
    main()



# file_transfer_status = Complete, Not Complete
