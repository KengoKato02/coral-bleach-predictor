import matplotlib.pyplot as plt
import numpy as np

# CAN DELETE:  Left this here for now in case for placeholder
def evaluate_model(predictions, ground_truth):
    """
    Evaluate model predictions by comparing to ground truth.
    """
    correct = 0
    total = len(ground_truth)
    
    for predicted, actual in zip(predictions, ground_truth):
        if predicted == actual:
            correct += 1
    
    accuracy = correct / total
    return accuracy

# CAN DELETE:  Left this here for now in case for placeholder
def visualize_data(data, title):
    """
    Visualize the data using matplotlib 
    """
    
    # First want to convert to numpy array because matplotlib
    np_array = np.array(data)
    grid_size = np_array.shape

    # Choose a categorical colormap (tab10 covers 10 colors; adjust if needed)
    cmap = plt.get_cmap('tab10')

    plt.figure(figsize=(grid_size[1] * 0.5, grid_size[0] * 0.5)) 
    plt.imshow(np_array, cmap=cmap, interpolation='none')

    plt.grid(which='both', color='gray', linewidth=1, linestyle='-', alpha=0.5)
    plt.xticks(np.arange(-0.5, grid_size[1], 1), [])
    plt.yticks(np.arange(-0.5, grid_size[0], 1), [])
    plt.gca().set_xticks(np.arange(-.5, grid_size[1], 1), minor=True)
    plt.gca().set_yticks(np.arange(-.5, grid_size[0], 1), minor=True)
    plt.gca().grid(which='minor', color='black', linewidth=1)
    plt.gca().tick_params(which='both', bottom=False, left=False, labelbottom=False, labelleft=False)

    plt.title(title)
    plt.tight_layout()
    plt.show()