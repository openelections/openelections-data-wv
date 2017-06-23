#!/usr/bin/env python3

"""Script for converting 2008 West Virgina county-level voting files from .xlsx to OpenElex .csv format"""

import os
import csv
import click
import re

from collections import namedtuple, defaultdict
from itertools import groupby
from openpyxl import load_workbook

from zipfile import BadZipfile

PrecinctRows = namedtuple('PrecinctRows', ['precinct', 'start', 'end'])
OfficeRegex = namedtuple('OfficeRegex', ['office', 'office_code', 'regex'])

OFFICE_TITLE_LOOKUP = {
    'U.S. President': 'President',
    'U.S. Senate': 'U.S. Senate',
    'U.S. House of Representatives': 'U.S. House',
    'Governor': 'Governor',
    'Secretary of State': 'Secretary of State',
    'State Treasurer': 'State Treasurer',
    'Auditor': 'State Auditor',
    'Commissioner of Agriculture': 'Commissioner of Agriculture',
    'Attorney General': 'Attorney General',
    'State Senate': 'State Senate',
    'House of Delegates': 'State House'
}

PARTY_LOOKUP = { 'D': 'DEM', 'R':'REP', 'M':'MTN', 'C': 'CON' }

COUNTY_TO_DISTRICT_LOOKUP = {'Barbour': '1', 'Berkeley': '2', 'Boone': '3', 'Brooke': '1', 'Braxton': '2', 'Cabell': '3', 'Doddridge': '1', 'Calhoun': '2', 'Fayette': '3', 'Gilmer': '1', 'Clay': '2', 'Greenbrier': '3', 'Grant': '1', 'Hampshire': '2', 'Lincoln': '3', 'Hancock': '1', 'Hardy': '2', 'Logan': '3', 'Harrison': '1', 'Jackson': '2', 'Mason': '3', 'Marion': '1', 'Jefferson': '2', 'McDowell': '3', 'Marshall': '1', 'Kanawha': '2', 'Mercer': '3', 'Mineral': '1', 'Lewis': '2', 'Mingo': '3', 'Monongalia': '1', 'Morgan': '2', 'Monroe': '3', 'Ohio': '1', 'Pendleton': '2', 'Nicholas': '3', 'Pleasants': '1', 'Putnam': '2', 'Pocahontas': '3', 'Preston': '1', 'Randolph': '2', 'Raleigh': '3', 'Ritchie': '1', 'Roane': '2', 'Summers': '3', 'Taylor': '1', 'Upshur': '2', 'Wayne': '3', 'Tucker': '1', 'Wirt': '2', 'Webster': '3', 'Tyler': '1\t', 'Wyoming': '3', 'Wetzel': '1', 'Wood': '1'}

def lookup_district(office, county):
    if office == 'U.S. House' or office == 'U.S. House of Representatives':
        return COUNTY_TO_DISTRICT_LOOKUP[county]
    else:
        return ''


def get_precinct_rows(sheet_rows):
    """Pass in a worksheet and yield a namedtuples containing the start and end rows for each precinct"""
    current_start = 0
    current_precinct = None
    for i, row in enumerate(sheet_rows):
        try:
            test_match = re.match(r"PRECINCT: (\d+)", row[0].value)
        except TypeError: # Skip over empty cells
            continue
        if test_match:
            if current_precinct is not None:
                yield PrecinctRows(precinct=current_precinct, start=current_start, end=i-1)
            current_precinct = test_match.group(1)
            current_start = i
    yield PrecinctRows(precinct=current_precinct, start=current_start, end=len(sheet_rows))

def get_contested_offices(precinct_rows):
    """Parse offices being contested in a given precinct.
    
    Accepts an array of rows and returns a dictionary mapping the office code to the office title.
    """
    offices_contested = {}
    parsing = False
    for i, row in enumerate(precinct_rows):
        try:
            if parsing:
                office_code, office, votes = [cell.value for cell in row if cell.value]
                if office_code == str(office_code):
                    offices_contested[office_code.rstrip()] = office.rstrip()
        except ValueError:
            parsing = False
        try:
            if re.match('TOTAL BY CONTEST', row[0].value):
                parsing = True
            if re.match('TOTAL BY CANDIDATE', row[0].value):
                parsing = False
        except TypeError:
            pass
    return offices_contested

def get_office_rows(offices, rows):
    """Parses precinct rows and returns a dictionary mapping each contested office to a list of rows with votes.
    
    Office results are not consistently contiguous. Using the office code to id a row with votes is more reliable.
    """
    office_rows = defaultdict(list)
    parsing = False
    for row in rows:
        if parsing:
            code = row[1].value
            if code:
                try:
                    clean_code = code.strip()
                except AttributeError:
                    continue
                try:
                    office_title = offices[clean_code]
                except KeyError:
                    continue
                if office_title in OFFICE_TITLE_LOOKUP:
                    office_rows[office_title].append(row)
        try:
            if re.match('TOTAL BY CANDIDATE', row[0].value):
                parsing = True
        except TypeError:
            pass
    return office_rows

def get_data(office_rows):
    """Extract party, candidate and vote count from a list of rows. Yields a tuple of party, candidate, and votes."""
    for row in office_rows:
        try:
            party, candidate = row[3].value.split(' - ')
        except AttributeError as e:
            pass
        party = PARTY_LOOKUP.get(party, '')
        candidate = candidate.strip()
        votes = row[5].value
        yield (party, candidate, votes)


def parse(sheet_rows):
    """Takes raw data from xlsx and yields processed results by precinct."""
    precinct_rows = get_precinct_rows(sheet_rows)
    for precinct in precinct_rows:
        p_rows = sheet_rows[precinct.start:precinct.end]
        contested_offices_lookup = get_contested_offices(p_rows)
        office_rows = get_office_rows(contested_offices_lookup, p_rows)
        for office, rows in office_rows.items():
            for party, candidate, votes in get_data(rows):
                yield (precinct.precinct, office, party, candidate, votes)

def rollup(converted_rows):
    """Takes parsed rows, computes the total for each candidate cast across all precincts, and adds totals to results"""
    totals = []
    converted_rows.sort(key=lambda x: x['candidate'])

    for key, group in groupby(converted_rows, key=lambda x: x['candidate']):
        group_rows = [row for row in group]
        total = sum([row['votes'] for row in group_rows])
        total_row = {}
        for k,v in group_rows[0].items():
            if k == 'precinct':
                total_row[k] = 'Total'
            elif k == 'votes':
                total_row[k] = total
            else:
                total_row[k] = v
        totals.append(total_row)
    combined = totals + converted_rows
    combined.sort(key=lambda x: x['office'])
    return combined

def convert_sheet(input_file, output_dir):
    click.echo(f'Loading {input_file}...')
    try:
        wb = load_workbook(input_file)
    except BadZipfile as e:
        click.echo(f'Skipping {input_file}. File format is not valid.')
        raise BadZipfile
    results_sheet = wb.get_sheet_by_name('Sheet1')
    sheet_rows = [row for row in results_sheet.rows]
    county = re.match(r"COUNTY NAME: (.+)", sheet_rows[0][0].value).group(1)

    output_filename = f'20081104__wv__general__{county.lower()}__precinct.csv'
    output_filepath = os.path.join(output_dir, output_filename)
    if os.path.exists(output_filepath):
        if not click.confirm(f'Results for {county} already exist. Do you want to continue?'):
            raise FileExistsError(f'Skipping {county}. Results already exist.\n')
    click.echo(f'Processing {county}...')
    converted = []
    for precinct, office, party, candidate, votes in parse(sheet_rows):
        converted.append({
            'county': county,
            'precinct': precinct,
            'office': OFFICE_TITLE_LOOKUP[office],
            'district': lookup_district(office, county),
            'party': party,
            'candidate': candidate,
            'votes': votes
        })
    converted_with_totals = rollup(converted)
    click.echo(f'Saving {county} results to {output_filepath}...\n')
    with open(output_filepath, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['county', 'precinct', 'office', 'district', 'party', 'candidate', 'votes'])
        writer.writeheader()
        writer.writerows(converted_with_totals)


@click.command()
@click.option('--input_dir', '-i', help='Input directory for files to convert',type=click.Path())
@click.option('--output_dir', '-o', help='Output directory for file to convert',type=click.Path())
def process(input_dir, output_dir):
    """Given an input directory and an output directory, will read and convert from xlsx to csv.
    
    Will prompt user for confirmation to overwrite output file if it already exists.
    """
    raw_workbooks = [f for f in os.listdir(input_dir) if f.endswith('.xlsx')]
    for workbook in raw_workbooks:
        workbook_file_path = os.path.join(input_dir, workbook)
        try:
            convert_sheet(workbook_file_path, output_dir)
        except BadZipfile:
            pass
        except FileExistsError as e:
            print(e)
            pass

if __name__ == '__main__':
    process()

