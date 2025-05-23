import os
import requests
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def load_noaa_data(file_path):
    """
    Read NOAA data from a CSV file.
    This function is a placeholder and should be replaced with actual data loading logic.
    """
    full_path = os.path.join(project_root, file_path)
    
    # Placeholder for NOAA data
    with open(full_path, "r") as file:
        for line in file:
            print(line)  # Just test for now
            
    
# i think this needs to be done in a better way
def load_noaa_station_data(url):
    response = requests.get(url)#

    lat = None
    lon = None
    data_start = 0
    headers = []
    station_name = ""
    
    # extract station name
    lines = response.text.split('\n')
    
    # Find the station name 
    for i, line in enumerate(lines):
        if i == 1 and line.strip():  # station name should be line 1
            station_name = line.strip()
            break

    # Match to the region based on the URL
    if 'gbr' in url:
        region = 'Great Barrier Reef'
    elif any(x in url for x in ['samoas', 'cook', 'hawaiian']):
        region = 'Polynesia'
    else:
        region = 'Caribbean'
    
    # Extract latitude and longitude from each set
    for i, line in enumerate(lines):
        if 'Latitude' in line and i+1 < len(lines):
            try:
                lat = float(lines[i+1].strip())
            except (ValueError, TypeError):
                pass
        if 'Longitude' in line and i+1 < len(lines):
            try:
                lon = float(lines[i+1].strip())
            except (ValueError, TypeError):
                pass
    
    
    # Find the data rows more robustly
    for i, line in enumerate(lines):
        if 'YYYY' in line and 'MM' in line and 'DD' in line:
            headers = line.split()
            data_start = i + 1
            break
    
    if not headers or data_start == 0:
        raise ValueError(f"Could not find data headers in {url}")
    
    data_rows = []
    
    # Read the data rows
    for line in lines[data_start:]:
        if line.strip():  # Skip empty lines
            row = line.split()
            if len(row) >= 3:  #we need YYYY, MM, DD
                if len(row) < len(headers):
                    row += [np.nan] * (len(headers) - len(row))
                row = row[:len(headers)]
                data_rows.append(row)
    
    df = pd.DataFrame(data_rows, columns=headers)
    
    # add station information
    df['Station'] = station_name if station_name else url.split('/')[-1].replace('.txt', '')
    df['Region'] = region
    df['Latitude'] = lat
    df['Longitude'] = lon
    
    return df