import os
import numpy as np
import pandas as pd
import torch as t
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

# Generate all possible pairs (a, b) and their modular subtraction results
def generate_exhaustive_modular_subtraction_data(mod, train_split=0.6, val_split=0.2):
    # Generate data
    a = np.arange(mod)
    b = np.arange(mod)
    A, B = np.meshgrid(a, b)
    X = np.column_stack((A.ravel(), B.ravel()))
    y = (X[:, 0] - X[:, 1]) % mod

    # Combine X and y for easier splitting
    data = np.column_stack((X, y))

    # Shuffle the data
    np.random.shuffle(data)

    # Split the data into train, validation, and test sets
    n_train = int(len(data) * train_split)
    n_val = int(len(data) * val_split)
    # n_test = len(data) - n_train - n_val

    train_data = data[:n_train]
    val_data = data[n_train:n_train + n_val]
    test_data = data[n_train + n_val:]

    # Create DataFrames
    train_df = pd.DataFrame(train_data, columns=['A', 'B', 'Result'])
    val_df = pd.DataFrame(val_data, columns=['A', 'B', 'Result'])
    test_df = pd.DataFrame(test_data, columns=['A', 'B', 'Result'])

    # Save DataFrames to CSV files
    train_df.to_csv(f'train_{mod}.csv', index=False)
    val_df.to_csv(f'val_{mod}.csv', index=False)
    test_df.to_csv(f'test_{mod}.csv', index=False)

    print(f"Datasets generated and saved to 'train_{mod}.csv', 'val_{mod}.csv', and 'test_{mod}.csv'")

# Load datasets from CSV files and create DataLoader objects
def load_dataloaders(mod, batch_size):
    # Check for CSV files and generate them if not available
    train_file = f'train_{mod}.csv'
    val_file = f'val_{mod}.csv'
    test_file = f'test_{mod}.csv'

    if not (os.path.exists(train_file) and os.path.exists(val_file) and os.path.exists(test_file)):
        generate_exhaustive_modular_subtraction_data(mod)

    # Load datasets from CSV files
    train_data = pd.read_csv(train_file)
    val_data = pd.read_csv(val_file)
    test_data = pd.read_csv(test_file)
    
    train_dataset = TensorDataset(t.tensor(train_data[['A', 'B']].values, dtype=t.float32),
                                  t.tensor(train_data['Result'].values, dtype=t.float32).view(-1, 1))
    val_dataset = TensorDataset(t.tensor(val_data[['A', 'B']].values, dtype=t.float32),
                                t.tensor(val_data['Result'].values, dtype=t.float32).view(-1, 1))
    test_dataset = TensorDataset(t.tensor(test_data[['A', 'B']].values, dtype=t.float32),
                                 t.tensor(test_data['Result'].values, dtype=t.float32).view(-1, 1))
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader, test_loader

# Define the MLP model
class MLP(nn.Module):
    def __init__(self,hn): # hn is for "hidden neurons"
        super().__init__()
        self.fc1 = nn.Linear(2, hn)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hn, 1)
    
    def forward(self, x):
        out = self.fc2(self.relu(self.fc1(x)))
        return out

# Train the model
def train(model, train_loader, val_loader, epochs=10, lr=0.001):
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    total_batches = epochs * (len(train_loader) + len(val_loader))
    with tqdm(total=total_batches, desc='Training Progress', leave=True) as pbar:
        for epoch in range(epochs):
            model.train()
            running_loss = 0.0
            for i, (inputs, labels) in enumerate(train_loader):
                optimizer.zero_grad()
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                running_loss += loss.item()
                avg_train_loss = running_loss / (i + 1)
                
                pbar.set_postfix({'Epoch': epoch + 1, 'Train Loss': avg_train_loss})
                pbar.update(1)

            model.eval()
            val_loss = 0.0
            with t.no_grad():
                for j, (inputs, targets) in enumerate(val_loader):
                    outputs = model(inputs)
                    loss = criterion(outputs, targets)
                    val_loss += loss.item()
                    avg_val_loss = val_loss / (j + 1)
                    
                    pbar.set_postfix({'Epoch': epoch + 1, 'Val Loss': avg_val_loss})
                    pbar.update(1)

            tqdm.write(f"Epoch [{epoch + 1}/{epochs}], Train Loss: {avg_train_loss:.4f}, Validation Loss: {avg_val_loss:.4f}")
    
    print("Training finished.")

# Evaluate the model
def evaluate(model, test_loader):
    model.eval()
    criterion = nn.MSELoss()
    total_loss = 0.0
    all_outputs = []
    all_targets = []
    
    with t.no_grad():
        for inputs, targets in test_loader:
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            total_loss += loss.item()
            all_outputs.append(outputs)
            all_targets.append(targets)
    
    all_outputs = t.cat(all_outputs)
    all_targets = t.cat(all_targets)
    total_mae = t.mean(t.abs(all_outputs - all_targets)).item()
    
    avg_loss = total_loss / len(test_loader)
    
    print(f"Test Loss: {avg_loss:.4f}, Mean Absolute Deviation: {total_mae:.4f}")
    return avg_loss, total_mae