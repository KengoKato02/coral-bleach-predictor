import matplotlib.pyplot as plt
from utils import visualize_data
from load import load_noaa_data

def main():
    """
    Main function here.
    Function will load data for the first task in the dataset
    and visualizes the first task input.
    Placeholder example for now.
    """
  
    # Hardcoded example to test for first file
    data_noaa = load_noaa_data("data/noaa/raw_data/southwestern_cuba.txt")

if __name__ == '__main__':
    main()