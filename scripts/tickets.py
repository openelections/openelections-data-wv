#!/usr/bin/env python3

'''
Returns every "ticket", a unique office-candidate pair,
from a given state-wide precinct file.

!! THIS IS THE WEST VIRGINIA VERSION OF THIS GENERAL SCRIPT !!
'''

from itertools import combinations, filterfalse
import pandas as pd
pd.set_option('mode.chained_assignment',None)
import numpy as np
from fuzzywuzzy import fuzz, process
from curtsies.fmtfuncs import red, bold, green, on_blue, yellow

class Tickets():
    
    # tokens representing e.g. void ballots or total vote counts
    PROCEDURALS = {
        'VOIDS': 'VOID',
        'BLANKS': 'BLANK',
        'TOTALS': 'BALLOTS',
        'TOTAL': 'BALLOTS',
        'TOTAL VOTES': 'BALLOTS',
        'BALLOTS CAST': 'BALLOTS',
        'OVER VOTES': 'OVER',
        'UNDER VOTES': 'UNDER',
        'SCATTERING': 'SCATTER'
    }
    PROCEDURALS_LIST = list(PROCEDURALS.keys()) + list(PROCEDURALS.values()) + [
        'UNCOMMITTED'
    ]
    # unwanted characters and their replacements
    BAD_CHARS = {
        '.': '',
        ',': '',
        ':': '',
        '"': '', # only for hanging quote marks
        '-': ' ',# since all quote sections cut first
        "'": ' ',
        '&': 'AND',
        '“': '',
        '”': ''
    }
    # delimiter characters
    DELIMS = ['/', '\\', ' AND ']
    
    # affixes to cut out of names
    # - parties, nicknames
    AFFIX = [r'^REP', r'^DEM', r'^IND', r'\".*\"', r'\(.*\)']

    def __init__(self, state_name: str, df: pd.DataFrame, year: str):
        # metadata
        self.state = state_name
        self.state_name = ' '.join(self.state.split('_')).title()
        self.year = year
        
        # data
        self.df = df[df.candidate.isna() == False]
        self.df = df[df.office.isna() == False]
    
        
    def parse(self) -> pd.DataFrame:
        '''
        Main runtime wrapper.
        '''
        # tickets
        self.tickets, self.ticket_changes = self.get_tickets(self.df)
        
        # match warnings
        self.match_warning(self.tickets)
        
        # saving to file
        self.save(self.tickets, self.ticket_changes)
        
        return self.tickets
    
    def get_tickets(self, df: pd.DataFrame) -> pd.DataFrame:
        '''
        Primary wrapper for parsing tickets:
        - cleans data
        - gets tickets
        - prints updates to console
        '''
        
        print('\n-----------------------------')
        print(f'Getting tickets for {on_blue(self.state_name)} in {on_blue(self.year)} ...')
        print('-----------------------------')
        
        c = df['candidate']
        o = df['office']
        
        print('CLEANING CANDIDATES ...')
        print('starting uniques:', red(str(len(c.unique()))))
        c = self.clean_names(c)
        c = self.tags(c)
        print('final uniques:', green(str(len(c.unique()))))
        
        print('CLEANING OFFICES ...')
        print('starting uniques:', red(str(len(o.unique()))))
        o = self.clean_offices(o)
        print('final uniques:', green(str(len(o.unique()))))
        
        df['candidate'] = c
        df['office'] = o
        
        # matching until clean, tracking iterations
        print('------------------------------')
        changes_list = []
        i = 1
        while True:
            df, changes, done = self.match(df, i)
            changes_list.append(changes)
            if done:
                break
            else:
                i += 1
        print('------------------------------')
        
        # assembling tickets
        offices = df.office.drop_duplicates().tolist()
        dt = []
        for o in offices:
            odf = df.groupby('office').get_group(o)
            candidates = odf.candidate.drop_duplicates().dropna().tolist()
            for c in candidates:
                d = odf.district[odf.candidate == c].unique()[0]
                p = odf.party[odf.candidate == c].unique()[0]
                dt.append((o,d,c,p))
        fdf = pd.DataFrame(dt, columns=['office','district','candidate','party'])
    
        # compiling changes
        change_df = pd.concat([pd.DataFrame(c, columns=['old', 'new', 'office']) for c in changes_list], 
                              keys=list(range(i)))
        change_df.index.names = ['iteration','ind']
        
        return fdf, change_df

    def clean_names(self, s: pd.Series) -> pd.Series:
        '''
        Standardizes formatting of candidate names.
        '''
        
        s = s.str.strip()
        s = s.str.upper()
        
        # bad characters
        for char, replacement in self.BAD_CHARS.items():
            s = s.str.replace(char, replacement, regex=False)
        
        # procedural tokens
        s = s.replace(self.PROCEDURALS)

        # splitting on delimiters
        col_split = lambda s, c: s.str.split(c, expand = True)[0]
        for c in self.DELIMS:
            s = col_split(s,c)
        
        # standardizing write-ins
        s = s.str.replace('WRITE IN ', 'WRITE INS ')
        
        # whitespace
        s = s.str.replace('\s+', ' ', regex=True)
        s = s.str.strip()
        
        return s
    
    def clean_offices(self, s: pd.Series) -> pd.Series:
        '''
        Standardizes office names.
        '''
        
        s = s.str.strip()
        s = s.str.upper()
        
        for char, replacement in self.BAD_CHARS.items():
            s = s.str.replace(char, replacement, regex=False)
            
        s = s.str.replace('\s+', ' ', regex=False)
        s = s.str.strip()
        
        return s
    
    def tags(self, s: pd.Series) -> pd.Series:
        '''
        Standardizes prefixes/suffixes often
        added to candidate names.
        '''
        
        # WRITE INS first, as they may include the others
        wr = s[s.str.contains('WRITE INS', na=False)]
        if not wr.empty:
            changes = {}
            for ind, name in wr.iteritems():
                w = name.partition('WRITE INS')
                if w[0] != '' and w[0] != 'UNQUALIFIED ':
                    new_name = w[0].strip()
                elif name == 'WRITE INS':
                    new_name = 'WRITE INS'            
                # collapsing "Unqualified write ins"
                elif w[0] == 'UNQUALIFIED ':
                    new_name = 'WRITE INS'
                changes[name] = new_name
            s = s.replace(changes)
        
        # cutting out unwanted affixes
        for a in self.AFFIX:
            s = s.str.replace(a, '', regex=True)
        
        return s
        
    def match(self, df: pd.DataFrame, iteration: int, verbose=False) -> pd.DataFrame:
        '''
        Fuzzy matches similar candidate names.
        '''
        print(f'FUZZY MATCHING | Iteration {iteration}')
        s = df['candidate']
        candidate_names = s.value_counts().index.tolist()
        
        # CHECK THAT MATCH PAIR IS VALID:
        # - score is at least 85
        # - not a self-match
        # - not a reverse match: re-matching an already changed token
        unique = lambda n,s: s >= 85 and n != name and n not in changes.values()
        
        changes = {}
        change_df = []
        for name in candidate_names:
            # checking if name not already matched as incorrect
            if name not in changes.keys():
                # fuzzy matches 
                scores = process.extract(name, candidate_names, scorer=fuzz.token_set_ratio)
                matches = [(n,s) for (n,s) in scores if unique(n,s)]
                if matches:
                    for match_pair in matches:
                        # if match_pair[0] not in changes.values():
                        match = match_pair[0]
                        name_office = df.office[df.candidate == name].tolist()[0]
                        match_office = df.office[df.candidate == match].tolist()[0]
                        if name_office == match_office:
                            changes[match] = name
                            change_df.append((match, name, name_office))
                            if verbose:
                                print(f'{red(match)} -- to --> {green(name)}')
                            
        # making changes to column
        s = s.replace(changes)
        df['candidate'] = s
        print(f'MADE {bold(str(len(changes.keys())))} CHANGES |','UNIQUES:', green(str(len((s.unique())))))
        
        # checking whether to continue
        done = False if len(changes) > 0 else True
        
        return df, change_df, done
    
    def match_warning(self, df: pd.DataFrame) -> list:
        '''
        Flags similar candidate names in the final get_tickets df
        that were not sufficient to match.
        '''
        print('Flagging potential (but unchanged) matches...')
        offices = df.office.unique()
        near_matches = []
        for office in offices:
            odf = df.groupby('office').get_group(office)
            candidates = odf['candidate'].tolist()
            for a,b in combinations(candidates, 2):
                if fuzz.ratio(a,b) >= 75:
                    print(yellow(f'near match: {a} & {b}'))
                    near_matches.append((a,b))
                    
        if near_matches:
            return near_matches
        else:
            return False
    
    def save(self, df: pd.DataFrame, change_df: pd.DataFrame) -> None:
        '''
        Saves data to file as CSVs.
        '''
        filename = f'{self.year}/{self.state}__{self.year}__tickets.csv'
        df.to_csv(filename)
        change_df.to_csv(f'{self.year}/{self.state}__{self.year}__ticket__changes.csv')
        
        print(f'Finished and saved to file at {filename}')
    