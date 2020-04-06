import pandas as pd
import numpy as np

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
            return "NA"
        # Test is NEGATIVE if no targets are positive AND MS2 is POSITIVE
        elif target_count == 0 and MS2 != "Undetermined":
            return "NEGATIVE"
        # Test is INCONCLUSIVE if ONLY ONE target is positive (regardless of MS2 status)
        elif target_count == 1:
            return "INCONCLUSIVE"
        # Test is POSITIVE if MORE THAN ONE target is positive (regardless of MS2 status)
        elif target_count > 1:
            return "POSITIVE"

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
    def get_results(self,file_path):
        self.read_file(file_path)
        return self.parse_results()
