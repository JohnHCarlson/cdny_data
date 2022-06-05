import requests
from humanize import number
from bs4 import BeautifulSoup
import pandas as pd

NUM_DISTRICTS = 26
FILENAME = "congressional_candidates.csv"

class District:
    
    district_number = None#
    pvi = None
    incumbent = None
    candidates = None#
    population = None#
    gender = None#
    race = None#
    ethnicity = None#
    median_income = None#
    distribution = None

    def __str__(self):
        print(self.district_number)
        print(self.pvi)
        print(self.incumbent)
        print(self.candidates)
        print(self.population)
        print(self.gender)
        print(self.race)
        print(self.ethnicity)
        print(self.median_income)
        print(self.distribution)
        return ""

def generate_district_nums():
    
    districts = []

    for i in range(1, NUM_DISTRICTS + 1):
        districts.append(number.ordinal(i))

    return districts

def get_ballotpedia(district_ordinal):

    page = requests.get(f"https://ballotpedia.org/New_York%27s_{district_ordinal}_Congressional_District")
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup

def get_wiki(district_ordinal):

    page = requests.get(f"https://en.wikipedia.org/wiki/New_York%27s_{district_ordinal}_congressional_district")
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup

def scrape_candidates(district, page):

    candidate_names = []
    
    latest_dem_primary = page.find(class_='race_header democratic') # Gets the latest table of primary candidates (class=votebox)
    votebox = latest_dem_primary.parent

    results_text = votebox.find('p', class_='results_text').contents

    for elements in results_text:
        if "2022" in elements:

            primary_candidates_table = votebox.find('table', class_='results_table') #Gets a list of candidate elements (class=results_row)
            table_body = primary_candidates_table.findChild('tbody')
            candidates = table_body.findChildren(class_='results_row')

            for candidate in candidates: #Iterates through list of candidate elements
                
                candidate_anchor = candidate.findChild('a') #Pulls candidate name (if it exists)
                if candidate_anchor:
                    candidate_name = candidate_anchor.contents
                    candidate_names.append(candidate_name[0])
    
    district.candidates = candidate_names

def scrape_census_info(district, page):

    leg_infobox = page.find(class_='leg-infobox') #Finding census data table
    census_table = leg_infobox.find(class_='census-table')
    table_body = census_table.find('tbody')
    table_rows = table_body.findChildren('tr')

    for row in table_rows: #Goes through each row to find relevant data
        row_header = row.find('th') #Header contains info on which data point we're at
        row_data = row.find('td') #Data contains data, duh
        if row_header.contents[0] == "Population": #Pulls population data
            district.population = row_data.contents[0]

        elif row_header.contents[0]  == "Gender": #Pulls gender data, combines into single string
            genders = []
            for element in row_data.findAll('div', class_='leg-infobox-block'):
                genders.append(element.contents[0])
            district.gender = '\n'.join(f"{gender}" for gender in genders)

        elif row_header.contents[0]  == "Race": #Pulls race data, combines into single string
            races = []
            for element in row_data.findAll('div', class_='leg-infobox-block'):
                races.append(element.contents[0])
            district.race = '\n'.join(f"{race}" for race in races)

        elif row_header.contents[0]  == "Ethnicity": #Pulls ethnicity data, only listed ethnicity is hispanic, so no need to iterate
            district.ethnicity  = row_data.contents[0]

        elif row_header.contents[0]  == "Median household income": #Pulls median household income
            district.median_income = row_data.contents[0]                        

def scrape_wiki_info(district, page):

    infobox = page.find(class_='infobox') #Finding infobox table
    infobox_body = infobox.find('tbody')
    infobox_rows = infobox.findChildren('tr')

    for row in infobox_rows: #Iterating through rows in infobox table

        row_header = None #Title for each row
        
        if row.findChild('a'): #Accounting for some rows containing anchor tags
            row_header = row.findChild('a').contents
        else:
            row_header = row.findChild('th').contents

        if row_header[0] == "Representative": #Finds incumbent name
            row_data = row.findChild('td')
            if row_data.findChild('a'):
                district.incumbent = row_data.findChild('a').contents[0]
            else:
                district.incumbent = "Vacant"

        elif row_header[0] == "Distribution": #Gets distribution 
            distributions = []

            row_data = row.findChild('td')
            distribution_list = row_data.findChild('ul')
            for element in distribution_list.findChildren('li'):
                distributions.append(element.contents[0])
                district.distribution = '\n'.join(f"{distribution}" for distribution in distributions)

        elif row_header[0] == "Cook PVI": #Gets PVI
            district.pvi = row.findChild('td').contents[0]
            
def scrape_district_info(district_num, district_ordinal):

    ballotpedia_page = get_ballotpedia(district_ordinal) #Gets top-level page data
    wiki_page = get_wiki(district_ordinal)

    district = District() #Generates each piece of the district object
    district.district_number = district_num

    scrape_candidates(district, ballotpedia_page) #Adds data points to each district
    scrape_census_info(district, ballotpedia_page)
    scrape_wiki_info(district, wiki_page)

    return district

def generate_dataframe(district):
    
    district_data = {
        'District Number': district.district_number,
        'PVI': district.pvi,
        'Incumbent': district.incumbent,
        'Candidates': district.candidates, 
        'Population': district.population,
        'Gender': district.gender,
        'Race': district.race,
        'Ethnicity': district.ethnicity,
        'Median Income': district.median_income,
        'Distribution': district.distribution
    }
    district_dataframe = pd.DataFrame(dict([(k, pd.Series(v, dtype=pd.StringDtype())) for k,v in district_data.items()]))
    return district_dataframe

def write_to_csv(dataframe):

    dataframe.to_csv(FILENAME, sep=',')

def main():

    district_ordinals = generate_district_nums() #generates district ordinals
    frames = []

    for i in range(1, NUM_DISTRICTS + 1): 
        district = scrape_district_info(i, district_ordinals[i - 1]) #scrapes district
        district_dataframe = generate_dataframe(district)
        frames.append(district_dataframe)
    districts = pd.concat(frames, ignore_index=False)
    write_to_csv(districts)

if __name__ == '__main__':
    main()
