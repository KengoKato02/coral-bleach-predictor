import pandas as pd
        
def create_noaa_date_column(df, year_col='YYYY', month_col='MM', day_col='DD', date_col='Date'):
    """
    Concatenates year, month, and day columns into a single datetime column.

    Parameters:
        df (pd.DataFrame): The DataFrame containing the date columns.
        year_col (str): The name of the year column. Default is 'YYYY'.
        month_col (str): The name of the month column. Default is 'MM'.
        day_col (str): The name of the day column. Default is 'DD'.
        date_col (str): The name of the resulting datetime column. Default is 'Date'.

    Returns:
        None: Modifies the DataFrame in place by adding the new datetime column.
    """
    df[date_col] = pd.to_datetime(
        df[year_col].astype(str) + '-' +
        df[month_col].astype(str).str.zfill(2) + '-' +
        df[day_col].astype(str).str.zfill(2),
        errors='coerce'
    )

def create_noaa_seasonal_column(df, season_col='Season'):
    """
    Creates a season column based on the date column.

    Parameters:
        df (pd.DataFrame): The DataFrame containing the date column.
        season_col (str): The name of the resulting season column. Default is 'Season'.

    Returns:
        None: Modifies the DataFrame in place by adding the new season column.
    """
    df[season_col] =df['MM'].apply(lambda x: 
        'Winter' if x in ['12', '01', '02'] else
        'Spring' if x in ['03', '04', '05'] else
        'Summer' if x in ['06', '07', '08'] else
        'Fall')