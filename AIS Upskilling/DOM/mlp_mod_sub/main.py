import argparse
import torch as t
import torch.nn as nn
import torch.optim as optim
from helper import generate_exhaustive_modular_subtraction_data, load_dataloaders, MLP, train, evaluate

def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Train and interact with MLP model for modular subtraction.")
    parser.add_argument('--mod', '-m', type=int, required=True, help="Modulus for subtraction")
    parser.add_argument('--epochs', '-e', type=int, default=10, help="Number of epochs for training")
    parser.add_argument('--lr', '-l', type=float, default=0.001, help="Learning rate")
    parser.add_argument('--batch_size', '-b', type=int, default=32, help="Batch size for training")
    parser.add_argument('--hn', type=int, default=100, help="Number of hidden neurons")
    args = parser.parse_args()
    
    train_loader, val_loader, test_loader = load_dataloaders(args.mod, args.batch_size)
    
    # Initialize model
    model = MLP(args.hn)
    
    # Train model
    train(model, train_loader, val_loader, epochs=args.epochs, lr=args.lr)
    
    # Evaluate model
    evaluate(model, test_loader)
    t.save(model.state_dict(), f"model_{args.mod}.pt")
    
    # User interaction loop
    model.eval()
    while input("Do you want to test the model with custom inputs? (y/n): ").lower() == 'y':
        a = int(input("Enter the first number (a) for a - b: "))
        b = int(input("Enter the second number (b) for a - b: "))
        
        real_result = (a - b) % args.mod
        model_input = t.tensor([[a, b]], dtype=t.float32)
        with t.no_grad():
            model_output = model(model_input).item()
        
        print(f"Real a - b (mod {args.mod}): {real_result}")
        print(f"Model output: {model_output:.4f}")
        print(f"Absolute error: {abs(real_result - model_output):.4f}")

if __name__ == "__main__":
    main()