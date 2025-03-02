import os
import numpy as np
import pandas as pd
import torch as t
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm
import matplotlib.pyplot as plt
import json

def create_directories():
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)

# Generate all possible pairs (a, b) and their modular subtraction results
# Labels will need to be interpreted as one-hot classes at some point
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
    train_df.to_csv(f'./data/train_{mod}.csv', index=False)
    val_df.to_csv(f'./data/val_{mod}.csv', index=False)
    test_df.to_csv(f'./data/test_{mod}.csv', index=False)

    print(f"Datasets generated and saved to 'train_{mod}.csv', 'val_{mod}.csv', and 'test_{mod}.csv'")

# Load datasets from CSV files and create DataLoader objects
def load_dataloaders(mod, batch_size, one_hot=False):
    # Check for CSV files and generate them if not available
    train_file = f'./data/train_{mod}.csv'
    val_file = f'./data/val_{mod}.csv'
    test_file = f'./data/test_{mod}.csv'

    if not (os.path.exists(train_file) and os.path.exists(val_file) and os.path.exists(test_file)):
        generate_exhaustive_modular_subtraction_data(mod)

    # Load datasets from CSV files
    train_data = pd.read_csv(train_file)
    val_data = pd.read_csv(val_file)
    test_data = pd.read_csv(test_file)

    # Result shape and type is different here for classification    
    x_train = t.tensor(train_data[['A', 'B']].values, dtype=t.float32)
    x_val = t.tensor(val_data[['A', 'B']].values, dtype=t.float32)
    x_test = t.tensor(test_data[['A', 'B']].values, dtype=t.float32)

    if one_hot:
        x_train = one_hot_encode_inputs(x_train,mod)
        x_val = one_hot_encode_inputs(x_val,mod)
        x_test = one_hot_encode_inputs(x_test,mod)
    
    y_train = t.tensor(train_data['Result'].values, dtype=t.long).view(-1)
    y_val = t.tensor(val_data['Result'].values, dtype=t.long).view(-1)
    y_test = t.tensor(test_data['Result'].values, dtype=t.long).view(-1)

    train_dataset = TensorDataset(x_train,y_train)
    val_dataset = TensorDataset(x_val, y_val)
    test_dataset = TensorDataset(x_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader, test_loader, train_dataset, val_dataset, test_dataset # Added datasets to return

def one_hot_encode_inputs(inputs, mod):
    """
    Converts a tensor of inputs with shape [N, 2] containing scalar values
    for A and B into a one-hot encoded tensor of shape [N, 2 * mod].
    
    Parameters:
        inputs (Tensor): A tensor of shape [N, 2] (floats representing integers).
        mod (int): The modulus, used to define the size of one-hot encoding.
    
    Returns:
        Tensor: A tensor of shape [N, 2 * mod] with one-hot encoded values.
    """
    # Convert float tensor to long for one-hot encoding
    inputs_int = inputs.to(t.int64)
    
    # One-hot encode each column independently.
    a_onehot = F.one_hot(inputs_int[:, 0], num_classes=mod).float()  # Shape: [N, mod]
    b_onehot = F.one_hot(inputs_int[:, 1], num_classes=mod).float()  # Shape: [N, mod]
    
    # Concatenate the one-hot encoded columns along the feature dimension.
    return t.cat([a_onehot, b_onehot], dim=1)

# Define the MLP model
# Now I need #(classes) = mod output neurons, and a softmax
class MLP(nn.Module):
    def __init__(self,hn_tuple,num_classes,input_dim=2): # hn is for "hidden neurons"
        super().__init__()
        layers = []
        
        prev_layer_hn = input_dim
        for hn in hn_tuple:
            layers.append(nn.Linear(prev_layer_hn,hn))
            layers.append(nn.ReLU())
            prev_layer_hn = hn

        layers.append(nn.Linear(prev_layer_hn, num_classes))
        self.net = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.net(x)

# Train the model
# Criterion changes to cross entropy loss here
def train(model, train_loader, val_loader, epochs=100, lr=0.001, wd=0):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
    
    total_batches = epochs * (len(train_loader) + len(val_loader))
    avg_val_loss = 100 # Just for first epoch, before first validation
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
                
                pbar.set_postfix({'Epoch': epoch + 1, 'Train Loss': avg_train_loss, 'Val Loss': avg_val_loss})
                pbar.update(1)

            model.eval()
            val_loss = 0.0
            with t.no_grad():
                for j, (inputs, targets) in enumerate(val_loader):
                    outputs = model(inputs)
                    loss = criterion(outputs, targets)
                    val_loss += loss.item()
                    avg_val_loss = val_loss / (j + 1)
                    
                    pbar.set_postfix({'Epoch': epoch + 1, 'Train Loss': avg_train_loss, 'Val Loss': avg_val_loss})
                    pbar.update(1)

            # tqdm.write(f"Epoch [{epoch + 1}/{epochs}], Train Loss: {avg_train_loss:.4f}, Validation Loss: {avg_val_loss:.4f}")
    
    print("Training finished.")

# Evaluate the model
# CrossEntropyLoss here too
def evaluate(model, test_loader):
    model.eval()
    criterion = nn.CrossEntropyLoss()
    total_loss = 0.0
    correct_predictions = 0
    total_samples = 0
    
    with t.no_grad():
        for inputs, targets in test_loader:
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            total_loss += loss.item()
            
            # Get predicted class indices
            _, predicted = t.max(outputs, 1) # [batch,class] -> [batch]
            
            # Calculate the number of correct predictions
            correct_predictions += (predicted == targets).sum().item()
            total_samples += targets.size(0)
    
    avg_loss = total_loss / len(test_loader)
    accuracy = correct_predictions / total_samples * 100  # Accuracy in percentage

    print(f"Loss: {avg_loss:.4f}, Accuracy: {accuracy:.2f}%")
    return avg_loss, accuracy

def show_test_examples(model, test_dataset, num_samples=5):
    """
    Displays a few test examples in a human readable way.
    If the inputs are one-hot encoded (i.e. a vector of length 2*mod), it decodes them 
    back to the original (A, B) pair.
    """
    show_results = input("Do you want to see the results (y/n)? ").strip().lower()
    if show_results != 'y':
        return

    model.eval()
    import numpy as np
    import torch as t

    indices = np.random.choice(len(test_dataset), num_samples, replace=False)

    random_samples = []
    random_targets = []
    for idx in indices:
        sample, target = test_dataset[idx]
        random_samples.append(sample)
        random_targets.append(target)

    # Stack the samples and targets for batch processing
    random_samples = t.stack(random_samples)
    random_targets = t.tensor(random_targets)

    with t.no_grad():
        outputs = model(random_samples)
        _, predictions = t.max(outputs, 1)

    # Display each sample
    for i in range(num_samples):
        sample = random_samples[i]
        # If the input is one-hot encoded, decode it.
        if sample.numel() > 2:
            # Assuming sample shape is [2*mod], deduce mod from the length.
            mod = sample.numel() // 2
            a_val = t.argmax(sample[:mod]).item()
            b_val = t.argmax(sample[mod:]).item()
            input_str = f"({a_val}, {b_val})"
        else:
            # Otherwise, simply display the sample as a list.
            input_str = f"{sample.tolist()}"

        print(f"Sample {i+1}:")
        print(f"  Input: {input_str}")
        print(f"  Correct Output: {random_targets[i].item()}")
        print(f"  Predicted Output: {predictions[i].item()}\n")

def run_experiments(moduli, hidden_layer_configs, batch_size, epochs, lr, results_file='results.json'):
    # Load existing results
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            results = json.load(f)
    else:
        results = {}

    for hidden_layers in hidden_layer_configs:
        hidden_layers_str = '_'.join(map(str, hidden_layers))
        
        if hidden_layers_str not in results:
            results[hidden_layers_str] = {
                'moduli': [],
                'accuracies': []
            }

        for mod in moduli:
            model_filename = f'./models/model_mod{mod}_hl{hidden_layers_str}.pt'
            if mod not in results[hidden_layers_str]['moduli']:
                print(f"Running experiment for modulus {mod} with hidden layers {hidden_layers}...")
                train_loader, val_loader, test_loader, _ = load_dataloaders(mod, batch_size)

                model = MLP(hidden_layers, mod)
                train(model, train_loader, val_loader, epochs=epochs, lr=lr)
                t.save(model.state_dict(), model_filename)
                avg_loss, accuracy = evaluate(model, test_loader)

                # Update results dictionary
                results[hidden_layers_str]['moduli'].append(mod)
                results[hidden_layers_str]['accuracies'].append(accuracy)

                results = sort_results(results)

                # Save results to file
                with open(results_file, 'w') as f:
                    json.dump(results, f, indent=4)

def sort_results(results):
    sorted_results = {}

    for hidden_layers, mod_acc_dict in results.items():
        moduli = mod_acc_dict["moduli"]
        accuracies = mod_acc_dict["accuracies"]
        
        # Zip them together, sort by moduli, and unzip
        mod_acc_pairs = sorted(zip(moduli, accuracies))
        sorted_moduli, sorted_accuracies = zip(*mod_acc_pairs)
        
        sorted_results[hidden_layers] = {
            "moduli": list(sorted_moduli),
            "accuracies": list(sorted_accuracies)
        }
    
    return sorted_results

def get_results(results_file='results.json'):
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            results = json.load(f)
            return results
    else:
        print("No results file available.")

def plot_results(results):
    for hidden_layers_str in results.keys():
        mods = results[hidden_layers_str]['moduli']
        accs = results[hidden_layers_str]['accuracies']
        plt.plot(mods, accs, label=hidden_layers_str)
    
    random_accs = [100/mod for mod in mods]
    plt.plot(mods, random_accs, label='random')
    
    plt.xlabel('Modulus')
    plt.ylabel('Accuracy (%)')
    plt.legend()
    plt.title('Accuracy vs. Modulus for Different Network Sizes')
    plt.savefig(f'plot_mods_and_sizes.png')