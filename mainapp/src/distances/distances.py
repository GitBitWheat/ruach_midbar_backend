from collections import defaultdict
import requests
from math import trunc
import json
import csv

distances_dict = defaultdict(lambda: defaultdict(lambda: -1))
city_2_code = defaultdict(lambda: -1)
code_2_city = defaultdict(lambda: -1)

try:
    with open('mainapp/src/distances/SETL_JUNC.csv', 'r', encoding='utf-8') as f:
        f_csv = csv.reader(f)
        for idx, row in enumerate(f_csv):
            if idx == 0:
                continue
            city_2_code[row[0]] = int(row[1])
            code_2_city[int(row[1])] = row[0]
except FileNotFoundError:
    print('File not found.')
except PermissionError:
    print('Permission denied.')
except IOError:
    print('Error reading file.')

# Goverment of Israel datastore CKAN API URL
api_url = 'https://data.gov.il/api/3/action/datastore_search'

# Distances Resource ID
resource_id = 'bc5293d3-1023-4d9e-bdbe-082b58f93b65'

def get_distances(origin, destinations):
    codes = [city_2_code[dest] for dest in destinations]
    codes.append(city_2_code[origin])
    codes = [code for code in codes if code != -1]

    filters = {
        'קוד מוצא': codes,
        'קוד יעד': codes,
    }
    
    # Make the API request
    try:
        response = requests.get(api_url, params={
            'id': resource_id,
            'fields': ['קוד מוצא,קוד יעד,מרחק ממרכז למרכז'],
            'filters': json.dumps(filters),
        })
        data = response.json()
        records = data['result']['records']
        get_dest = lambda record: \
            code_2_city[record['קוד מוצא']] \
            if record['קוד מוצא'] != city_2_code[origin] \
            else code_2_city[record['קוד יעד']]
        dists = {
            get_dest(record): trunc(record['מרחק ממרכז למרכז']) \
            for record in records
        } 
        return dists
    except requests.exceptions.HTTPError as err:
        print(f'Distances HTTP Error:\n{err}\nReturning empty')
        return dict()
    except Exception as err:
        print(f'Distances unknown Error:\n{err}\nReturning empty')
        return dict()