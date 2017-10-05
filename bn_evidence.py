# -*- coding: utf-8 -*-
"""
Created on Sun Jul 23 13:59:37 2017

@author: CKAN
"""

import pandas as pd
import numpy as np
import json
from socios import buildFeatureFrame
import os
from pathlib import Path

src_dir = str(Path(__file__).parents[0])
dlrdb_dir = str(Path(__file__).parents[1])
output_dir = os.path.join(dlrdb_dir, 'output')

#List of random variables in Bayesian network
bn_n = ["monthly_income", "water_access", "roof_material", "wall_material", "cb_size", "floor_area", "geyser_nr"]

def evidence2000(year):
    """
    This function generates a json formatted evidence text file compatible with the syntax for providing evidence the python library libpgm for the specified year.
    """
    
    #Define socio-demographic search terms corresponding to BN nodes - valid for surveys from 2000 onwards
    searchlist = ['earn per month', 'watersource', 'GeyserNumber', 'GeyserBroken', 'roof', 'wall', 'main switch', 'floor area']
    
    #Get data and questions from socio-demographic survey responses
    data = buildFeatureFrame(searchlist, year)
    featureframe = data[0]
    
    featureframe['geyser_nr'] = featureframe['115'] - featureframe['131'] #geyser_nr = GeyserNumber - GeyserBroken
    featureframe.drop(['115','131'], axis=1, inplace=True) #remove superfluous geyser columns
    featureframe.columns = ['AnswerID'] + bn_n #rename columns to BN node names
    
    #Convert columns into datatypes that match BN node variables    
    income_bins = [0, 1800, 3200, 7800, 11600, 19116, 24500, 65600, 500000]
    income_labels = ['R0-R1799','R1800-R3199','R3200-R7799','R7800-R11599','R11600-R19115','R19116-R24499','R24500-R65499','+R65500']
    floorarea_bins = [0, 50, 80, 150, 250, 500]
    floorarea_labels = ["0-50", "50-80", "80-150","150-250","250-500"]

    featureframe.monthly_income = pd.cut(featureframe.monthly_income, bins = income_bins, labels = income_labels, right=False, include_lowest=True)
    featureframe.floor_area = pd.cut(featureframe.floor_area, bins = floorarea_bins, labels = floorarea_labels)
    
    featureframe.water_access = featureframe.water_access.map('{:.0f}'.format, na_action=None)
    featureframe.roof_material = featureframe.roof_material.map('{:.0f}'.format, na_action=None)
    featureframe.wall_material = featureframe.wall_material.map('{:.0f}'.format, na_action=None)
    featureframe.cb_size = featureframe.cb_size.map('{:.0f}'.format, na_action=None)
    featureframe.geyser_nr = featureframe.geyser_nr.map('{:.0f}'.format, na_action=None)
    featureframe.AnswerID = featureframe.AnswerID.map('{:.0f}'.format, na_action=None)
    
    featureframe.replace(np.nan, '', regex=True, inplace=True) #easier to remove empty string later than nan, which can behave unpredictably
    featureframe.set_index('AnswerID', inplace=True) #set AnswerID column as index
    
    #Convert dataframe into a dict formatted for use as evidence in libpgm BN inference
    featuredict = featureframe.to_dict('index') 
    e = []
    for f in featuredict.values(): 
        d = dict()
        for k,v in f.items():
            if v is not str(''):
                d[k] = v
        e.append(d)  
    evidence = dict(zip(featuredict.keys(), e))
    
    #Generate evidence file
    filename = 'bn_evidence_' + str(year) + '.txt'
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(evidence, f)
    print(filename + ' successfully saved to ' + output_dir)
    
    return #evidence