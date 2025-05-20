import matplotlib.pyplot as plt
import torch
from sklearn.model_selection import train_test_split
from utils import visualize_data
from load import load_arc_agi_data

def main():
    """
    Main function here.
    Function will load data for the first task in the dataset
    and visualizes the first task input.
    Placeholder example for now.
    """
  
    # Hardcoded example to test for first file
    data = load_arc_agi_data("data/ARC-AGI-1/training/0a938d79.json")

    # Split the data
    train_set = data['train']
    test_set = data['test']

    # Load to tensors
    sample = train_set[0]
    inputs = torch.tensor(sample['input'], dtype=torch.uint16)
    targets = torch.tensor(sample['output'], dtype=torch.uint16)

    # print(f"Device {inputs.device}"
    visualize_data(inputs, title="Input Grid")
    visualize_data(targets, title="Output Grid")

if __name__ == '__main__':
    main()