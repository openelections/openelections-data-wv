import os
import glob
import csv

def generate_headers(year, path):
    os.chdir(year)
    vote_headers = []
    for fname in glob.glob(path):
        with open(fname, "r") as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)
            print(list(fname + ': ' + h for h in headers if h not in ['county','precinct', 'office', 'district', 'candidate', 'party']))

def generate_offices(year, path):
    os.chdir(year)
    offices = []
    for fname in glob.glob(path):
        with open(fname, "r") as csvfile:
            print(fname)
            reader = csv.DictReader(csvfile)
            for row in reader:
                if not row['office'] in offices:
                    offices.append(row['office'])
    with open('offices.csv', "w") as csv_outfile:
        outfile = csv.writer(csv_outfile)
        outfile.writerows(offices)

def generate_consolidated_file(year, path, output_file):
    results = []
    os.chdir(year)
    os.chdir('counties')
    for fname in glob.glob(path):
        with open(fname, "r") as csvfile:
            print(fname)
            reader = csv.DictReader(csvfile)
            for row in reader:
                results.append([row['county'], row['precinct'], row['office'], row['district'], row['candidate'], row['party'], row['votes']])
    os.chdir('..')
    os.chdir('..')
    with open(output_file, "w") as csv_outfile:
        outfile = csv.writer(csv_outfile)
        outfile.writerow(['county','precinct', 'office', 'district', 'candidate', 'party', 'votes', 'vtd'])
        outfile.writerows(results)


@click.group()
def cli():
    pass


@cli.command('headers')
@click.argument('year')
@click.argument('election')
def headers_cmd(year, election):
    """Print non-standard headers found in precinct CSVs for ELECTION in YEAR."""
    generate_headers(year, election + '*precinct.csv')


@cli.command('offices')
@click.argument('year')
@click.argument('election')
def offices_cmd(year, election):
    """Write unique office names from precinct CSVs for ELECTION in YEAR to offices.csv."""
    generate_offices(year, election + '*precinct.csv')


@cli.command('consolidate')
@click.argument('year')
@click.argument('election')
@click.argument('election_type', default='general')
def consolidate_cmd(year, election, election_type):
    """Consolidate all precinct CSVs for ELECTION in YEAR into a single statewide file."""
    output_file = election + '__wv__' + election_type + '__precinct.csv'
    generate_consolidated_file(year, election + '*precinct.csv', output_file)
    click.echo(f"Written to {output_file}")


if __name__ == '__main__':
    cli()
