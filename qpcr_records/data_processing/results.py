import pandas as pd
import numpy as np
import boto3
import os
import sys
from io import StringIO
from decouple import config

class Results:

    def __init__(self):
        pass

    def read_file(self,file_path):
        print("Reading file")
        try:
            # Warning each run of this can take ~30 seconds because reading excel files is super slow and wasteful
            # Find how long the header of the file is to ignore when reading into Pandas
            tmp = pd.read_excel(file_path,sheet_name="Results")
            self.instrument_id = tmp.iloc[tmp[tmp['Block Type']=='Instrument Serial Number'].index[0],1]
            # Read in the file cleanly
            self.results = pd.read_excel(file_path,sheet_name="Results",skiprows=list(range(0,(list(tmp.iloc[:,0]).index("Well") + 1))))
            print("Results stored")
        # Just in case there is a typo that will throw everything off. I'd rather everything crash than return bad results
        except:
            print("ERROR READING FILE")

    # Decision tree for calling test result
    def diagnosis(self,r_dict):
        MS2 = r_dict["MS2"]
        covid_targets = ["N gene","ORF1ab","S gene"]
        # how many covid gene targets are positive?
        target_count = 3 - [r_dict[x] for x in covid_targets].count(-1.0)
        # Test is NA if no targets are positive AND MS2 is NEGATIVE
        if target_count == 0 and MS2 == -1.0:
            return "Invalid"
        # Test is NEGATIVE if no targets are positive AND MS2 is POSITIVE
        elif target_count == 0 and MS2 != -1.0:
            return "Negative"
        # Test is INCONCLUSIVE if ONLY ONE target is positive (regardless of MS2 status)
        elif target_count == 1:
            return "Inconclusive"
        # Test is POSITIVE if MORE THAN ONE target is positive (regardless of MS2 status)
        elif target_count > 1:
            return "Positive"

    def parse_results(self):
        print("Parsing results")
        wells = list(np.unique(self.results['Well Position']))
        targets = ["MS2","N gene","ORF1ab","S gene"]
        results_dict = {}
        for well in wells:
            df = self.results[self.results['Well Position'] == well].set_index("Target Name")
            r_dict = {}
            for target in targets:
                val = df.loc[target]["CRT"]
                conf = df.loc[target]["Cq Conf"]
                amp = df.loc[target]["Amp Status"]
                # double check confidence score and values
                if val != 'Undetermined':
                    # MS2 spike in is diluted now so it'll have degraded performance
                    # Making MS2 Cq_conf cutoff 0.5
                    if target == 'MS2':
                        if val > 0 and val < 40 and conf > 0.3:
                            val = round(val,3)
                        else:
                            val = -1.0
                    # Normal Cq_conf cutoff is 0.8
                    else:
                        if val > 0 and val < 40 and conf > 0.8:
                            val = round(val,3)
                        else:
                            val = -1.0
                else:
                    val = -1.0
                r_dict[target] = val
            r_dict["diagnosis"] = self.diagnosis(r_dict)
            results_dict[well]=r_dict
        # Finally add instrument id to dictionary
        results_dict['instrument'] = self.instrument_id
        print("Results successfully parsed")
        return results_dict

    # Call this function to get a nested dictionary of results indexed as follows:
    # {well position: {target1:value,target2:value,...,'diagnosis':value}}
    def get_results(self,object_key):
        #self.pull_from_s3(object_key)
        self.pull_from_django(object_key)
        return self.parse_results()

    def pull_from_s3(self,file_name):
        # get AWS credentials
        # NOTE: double check credentials
        s3 = boto3.resource('s3', region_name=config('AWS_S3_REGION_NAME'),
                            aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
                            aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'))
        bucket = s3.Bucket(config('AWS_STORAGE_BUCKET_NAME'))
        obj = bucket.Object(key=file_name)
        self.read_file(obj['Body'])

    def pull_from_django(self,file):
        print("Reading file")
        tmp = pd.read_excel(file,sheet_name="Results")
        self.instrument_id = tmp.iloc[tmp[tmp['Block Type']=='Instrument Serial Number'].index[0],1]
        # Read in the file cleanly
        self.results = pd.read_excel(file,sheet_name="Results",skiprows=list(range(0,(list(tmp.iloc[:,0]).index("Well") + 1))))
        print("Results stored")

    def read_fake_names(self):
        self.names_df = pd.read_csv('qpcr_records/data_processing/unique_psuedo_names_and_codes_04082020-v2-0_49999.csv').set_index('Barcode')

    def get_fake_name(self,barcode):
        try:
            return self.names_df.loc[barcode]['Last, First']
        except:
            return 'None'
