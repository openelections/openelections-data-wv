import clarify
import click
import re
import requests
import zipfile
import csv
from pathlib import Path

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO, BytesIO

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
    'Referer': 'https://results.enr.clarityelections.com/',
}

CLARITY_BASE_URL = 'https://results.enr.clarityelections.com/WV/{}/'

OFFICE_MAP = {
    'PRESIDENT': 'President',
    'U.S. PRESIDENT': 'President',
    'U.S. SENATOR': 'U.S. Senate',
    'U.S. HOUSE OF REPRESENTATIVES': 'U.S. House',
    'STATE SENATOR': 'State Senate',
    'HOUSE OF DELEGATES': 'State House',
    'GOVERNOR': 'Governor',
    'ATTORNEY GENERAL': 'Attorney General',
    'SECRETARY OF STATE': 'Secretary of State',
    'STATE TREASURER': 'State Treasurer',
    'TREASURER': 'State Treasurer',
    'AUDITOR': 'Auditor',
    'COMMISSIONER OF AGRICULTURE': 'Commissioner of Agriculture',
    'SUPERINTENDENT OF SCHOOLS': 'Superintendent of Schools',
    'NON-PARTISAN ELECTION OF JUDGE OF THE INTERMEDIATE COURT OF APPEALS': 'Intermediate Court of Appeals',
    'NON': 'Supreme Court of Appeals',
}

def normalize_office(office, district):
    """Map raw office/district strings to normalized names and a bare district number."""
    normalized = office
    for key, value in OFFICE_MAP.items():
        if office.upper().startswith(key):
            normalized = value
            break

    if district:
        m = re.search(r'\d+', str(district))
        district_num = m.group() if m else None
    else:
        district_num = None

    return normalized, district_num

def resolve_url(election_id_or_url):
    """Accept either a full Clarity results URL or a bare WV election ID and return a URL.

    The clarify library only looks for county subjurisdictions via its JSON
    electionsettings endpoint when the string 'web.' appears in the URL, so a
    placeholder 'web.0' segment is appended for bare election IDs to trigger
    that code path; the actual current report version is resolved separately.
    """
    if '://' in election_id_or_url:
        return election_id_or_url
    return CLARITY_BASE_URL.format(election_id_or_url) + 'web.0/'

def statewide_results(url, output_file):
    j = clarify.Jurisdiction(url=url, level="state")
    r = requests.get(j.report_url('xml'), headers=HEADERS, stream=True)
    z = zipfile.ZipFile(BytesIO(r.content))
    z.extractall()
    p = clarify.Parser()
    p.parse("detail.xml")
    results = []
    for result in p.results:
        candidate = result.choice.text
        office, district = parse_office(result.contest.text)
        party = result.choice.party
#        if '(' in candidate and party is None:
#            if '(I)' in candidate:
#                if '(I)(I)' in candidate:
#                    candidate = candidate.split('(I)')[0]
#                    party = 'I'
#                else:
#                    candidate, party = candidate.split('(I)')
#                candidate = candidate.strip() + ' (I)'
#            else:
#                print(candidate)
#                candidate, party = candidate.split('(', 1)
#                candidate = candidate.strip()
#            party = party.replace(')','').strip()
        if result.jurisdiction:
            county = result.jurisdiction.name
        else:
            county = None
        r = [x for x in results if x['county'] == county and x['office'] == office and x['district'] == district and x['party'] == party and x['candidate'] == candidate]
        if r:
             r[0][result.vote_type] = result.votes
        else:
            results.append({ 'county': county, 'office': office, 'district': district, 'party': party, 'candidate': candidate, result.vote_type: result.votes})

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "wt") as csvfile:
        w = csv.writer(csvfile)
        w.writerow(['county', 'office', 'district', 'party', 'candidate', 'votes'])
        for row in results:
            if row['county'] is None:
                continue
            office, district = normalize_office(row['office'], row['district'])
            total_votes = row['Election Day']# + row['Absentee by Mail'] + row['Advance in Person'] + row['Provisional']
            w.writerow([row['county'], office, district, row['party'], row['candidate'], total_votes])

def download_county_files(url, filename):
    no_xml = []
    j = clarify.Jurisdiction(url=url, level="state")
    subs = j.get_subjurisdictions()
    for sub in subs:
        report_url = sub.report_url('xml')
        if report_url is None:
            print(f"{sub.name}: no XML report available, skipping")
            no_xml.append(sub.name)
            continue
        try:
            r = requests.get(report_url, headers=HEADERS, stream=True)
            z = zipfile.ZipFile(BytesIO(r.content))
            z.extractall()
            precinct_results(sub.name.replace(' ','_').lower(), filename)
        except Exception as e:
            print(f"{sub.name}: failed ({e})")
            no_xml.append(sub.name)

    print("Counties without results:", no_xml)

def precinct_results(county_name, filename):
    f = filename + '__' + county_name + '__precinct.csv'
    p = clarify.Parser()
    p.parse("detail.xml")
    results = []
    vote_types = []
    for result in [x for x in p.results if not 'Number of Precincts' in x.vote_type]:
        vote_types.append(result.vote_type)
        if result.choice is None:
            continue
        candidate = result.choice.text
        office, district = parse_office(result.contest.text)
        party = result.choice.party #parse_party(result.contest.text)
#        if '(' in candidate and party is None:
#            if '(I)' in candidate:
#                if '(I)(I)' in candidate:
#                    candidate = candidate.split('(I)')[0]
#                    party = 'I'
#                else:
#                    candidate, party = candidate.split('(I)')
#            else:
#                candidate, party = candidate.split('(', 1)
#                candidate = candidate.strip()
#            party = party.replace(')','').strip()
        county = p.region
        if result.jurisdiction:
            precinct = result.jurisdiction.name
        else:
            precinct = None
        if precinct == None:
            continue
        r = [x for x in results if x['county'] == county and x['precinct'] == precinct and x['office'] == office and x['district'] == district and x['party'] == party and x['candidate'] == candidate]
        if r:
             r[0][result.vote_type] = result.votes
        else:
            results.append({ 'county': county, 'precinct': precinct, 'office': office, 'district': district, 'party': party, 'candidate': candidate, result.vote_type: result.votes})

    vote_types = list(set(vote_types))
    print(vote_types)
    vote_types.remove('regVotersCounty')
#    vote_types.remove('underVotes')
    with open(f, "wt") as csvfile:
        w = csv.writer(csvfile)
        headers = ['county', 'precinct', 'office', 'district', 'party', 'candidate', 'votes'] #+ [x.replace(' ','_').lower() for x in vote_types]
        w.writerow(headers)
        for row in results:
            if 'Republican' in row['office']:
                row['party'] = 'REP'
            elif 'Democrat' in row['office']:
                row['party'] = 'DEM'
            office, district = normalize_office(row['office'], row['district'])
            total_votes = sum([row[k] for k in vote_types if row[k]])
            w.writerow([row['county'], row['precinct'], office, district, row['party'], row['candidate'], total_votes])# + [row[k] for k in vote_types])


def parse_office(office_text):
    if ' - ' in office_text:
        office = office_text.split('-')[0]
    else:
        office = office_text.split(',')[0]
    if ', District' in office_text:
        district = office_text.split(', District')[1].split(' - ')[0].strip()
    elif 'United States Senator' in office_text:
        office = 'United States Senator'
        district = None
    elif ',' in office_text:
        district = office_text.split(',')[1]
    else:
        district = None
    return [office.strip(), district]

def parse_party(office_text):
    if '- REP' in office_text:
        party = 'REP'
    elif '- DEM' in office_text:
        party = 'DEM'
    else:
        party = None
    return party


@click.group()
def cli():
    pass


@cli.command('statewide')
@click.argument('election_id_or_url')
@click.argument('output_file')
def statewide_cmd(election_id_or_url, output_file):
    """Download statewide county-level results and write to OUTPUT_FILE.

    ELECTION_ID_OR_URL may be a full Clarity results URL (e.g.
    https://results.enr.clarityelections.com/WV/126209/web.345435/#/summary)
    or a bare WV election ID (e.g. 126209).
    """
    statewide_results(resolve_url(election_id_or_url), output_file)


@cli.command('precincts')
@click.argument('election_id_or_url')
@click.argument('filename')
def precincts_cmd(election_id_or_url, filename):
    """Download precinct-level results for all counties.

    ELECTION_ID_OR_URL may be a full Clarity results URL (e.g.
    https://results.enr.clarityelections.com/WV/126209/web.345435/#/summary)
    or a bare WV election ID (e.g. 126209).
    """
    download_county_files(resolve_url(election_id_or_url), filename)


if __name__ == '__main__':
    cli()
