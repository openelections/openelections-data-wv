import os
import glob
import pandas as pd
from tickets import Tickets

'''
Navigates through available general precinct files 
to parse tickets with tickets.py

!! THIS IS THE WEST VIRGINIA VERSION OF THIS GENERAL SCRIPT !!
'''

def get_files():
    '''
    Finds general precinct csv filenames from
    the parent dirrectory for parsing.
    '''
    os.chdir('../')
    filenames = glob.glob('**/*.csv')
    file_list = [f for f in filenames if '__general__' in f]
    file_dict = {}
    for f in file_list:
        year = f[:4]
        if year in file_dict.keys():
            file_dict[year].append(f)
        elif year not in file_dict.keys():
            file_dict[year] = [f]

    return file_dict

def format_files(filenames):
    '''
    Combines general office-specific files for the same year
    into a single DF for parsing.
    '''
    df_dict = {}
    for year, files in filenames.items():
        dfs = [pd.read_csv(f) for f in files]
        df = pd.concat(dfs)
        df_dict[year] = df
        
    return df_dict
        
def parse_files(dfs):
    '''
    Parses each given DataFrame for tickets.
    '''
    tickets_list = []
    for year, df in dfs.items():
        # main call
        parser = Tickets(state_name='west_virginia', df=df, year=year)
        tickets = parser.parse()
        tickets_list.append(tickets)

    return tickets_list

if __name__ == '__main__':
    files = get_files()
    dfs = format_files(files)
    tickets = parse_files(dfs)