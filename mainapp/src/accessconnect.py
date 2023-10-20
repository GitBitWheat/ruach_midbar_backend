import pyodbc
import os.path
import json



tables = dict()

try:
    with open('mainapp/src/tables.json', 'r', encoding='utf-8') as f_tables:
        tables = json.load(f_tables)
except FileNotFoundError:
    print('File not found.')
except PermissionError:
    print('Permission denied.')
except IOError:
    print('Error reading file.')

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), r'..\data\omri_db.accdb'))
print(f'db_path:  {db_path}')
def create_connection():
	return pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + db_path)

