import argparse
import torch as t
import torch.nn as nn
import torch.optim as optim
from helper import create_directories,generate_exhaustive_modular_subtraction_data, load_dataloaders, MLP, train, evaluate, show_test_examples

def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Train and interact with MLP model for modular subtraction.")
    parser.add_argument('--mod', '-m', type=int, required=True, help="Modulus for subtraction")
    parser.add_argument('--epochs', '-e', type=int, default=10, help="Number of epochs for training")
    parser.add_argument('--lr', '-l', type=float, default=0.001, help="Learning rate")
    parser.add_argument('--batch_size', '-b', type=int, default=32, help="Batch size for training")
    parser.add_argument('--hn', type=int, default=100, help="Number of hidden neurons")
    args = parser.parse_args()

    create_directories()
    
    train_loader, val_loader, test_loader, test_dataset = load_dataloaders(args.mod, args.batch_size)
    
    # Initialize model
    model = MLP(args.hn, args.mod) # New: this takes mod as input, to get num_classes 
    
    # Train model
    train(model, train_loader, val_loader, epochs=args.epochs, lr=args.lr)
    
    # Evaluate model
    evaluate(model, test_loader)
    t.save(model.state_dict(), f"./models/model_{args.mod}.pt")

    show_test_examples(model,test_dataset)

if __name__ == "__main__":
    main()