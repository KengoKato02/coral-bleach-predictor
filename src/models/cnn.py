import torch
import torch.nn as nn

class ARC_CNN(nn.Module):
    def __init__(self, input_channels=1, num_classes=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(input_channels, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, num_classes, kernel_size=1)  # Output: (batch, num_classes, H, W)
        )

    def forward(self, x):
        return self.net(x)
