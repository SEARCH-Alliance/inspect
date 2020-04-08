import pandas as pd
import numpy as np
import boto3
import os
import sys
from io import StringIO

class Results:

    def __init__(self):
        pass

    def read_file(self,file_path):
        print("Reading file")
        try:
            # Warning each run of this can take ~30 seconds because reading excel files is super slow and wasteful
            # Find how long the header of the file is to ignore when reading into Pandas
            tmp = pd.read_excel(file_path,sheet_name="Results")
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
        target_count = 3 - [r_dict[x] for x in covid_targets].count("Undetermined")
        # Test is NA if no targets are positive AND MS2 is NEGATIVE
        if target_count == 0 and MS2 == "Undetermined":
            return "Invalid"
        # Test is NEGATIVE if no targets are positive AND MS2 is POSITIVE
        elif target_count == 0 and MS2 != "Undetermined":
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
                r_dict[target] = df.loc[target]["CT"]
            r_dict["diagnosis"] = self.diagnosis(r_dict)
            results_dict[well]=r_dict
        print("Results successfully parsed")
        return results_dict

    # Call this function to get a nested dictionary of results indexed as follows:
    # {well position: {target1:value,target2:value,...,'diagnosis':value}}
    def get_results(self,object_key):
        self.pull_from_s3(object_key)
        return self.parse_results()

    def pull_from_s3(self,object_key):
        # get AWS credentials
        # NOTE: double check credentials
        aws_id = os.environ['AWS_ID']
        aws_secret = os.environ['AWS_SECRET']
        client = boto3.client('s3',aws_access_key_id=aws_id,
                              aws_secret_access_key=aws_secret)
        # NOTE: set proper bucket name
        bucket_name = 'put_bucket_name_here'
        excel_obj = client.get_object(Bucket=bucket_name,Key=object_key)
        body = csv_obj['Body']
        excel_string = body.read().decode('utf-8')
        self.read_file(StringIO(excel_string))
