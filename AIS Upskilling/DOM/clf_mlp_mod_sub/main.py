import argparse
import torch as t
import torch.nn as nn
import torch.optim as optim
from helper import *

def single_run():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Train and interact with MLP model for modular subtraction.")
    parser.add_argument('--mod', '-m', type=int, required=True, help="Modulus for subtraction")
    parser.add_argument('--epochs', '-e', type=int, default=10, help="Number of epochs for training")
    parser.add_argument('--lr', '-l', type=float, default=0.001, help="Learning rate")
    parser.add_argument('--batch_size', '-b', type=int, default=32, help="Batch size for training")
    parser.add_argument('--hn', type=int, default=100, help="Number of hidden neurons")
    args = parser.parse_args()

    train_loader, val_loader, test_loader, train_dataset, val_dataset, test_dataset = load_dataloaders(args.mod, args.batch_size)
    
    # Initialize model
    model = MLP(args.hn, args.mod) # New: this takes mod as input, to get num_classes 
    
    # Train model
    train(model, train_loader, val_loader, epochs=args.epochs, lr=args.lr)
    
    # Evaluate model
    evaluate(model, test_loader)
    t.save(model.state_dict(), f"./models/model_{args.mod}.pt")

    show_test_examples(model,test_dataset)

def experiment():
    parser = argparse.ArgumentParser(description='Run experiments with different network configurations.')
    parser.add_argument('-m', '--moduli', type=int, nargs='+', default=[5, 7, 9],
                        help='List of modulus values for experiments.')
    parser.add_argument('-hl', '--hidden_layers', type=str, nargs='+', default=['4', '8', '4,4', '8,4'],
                        help='List of hidden layer configurations. Each configuration should be a comma-separated string of integers.')
    parser.add_argument('-b', '--batch_size', type=int, default=32, help='Batch size for training.')
    parser.add_argument('-e', '--epochs', type=int, default=50, help='Number of training epochs.')
    parser.add_argument('-l', '--lr', type=float, default=0.001, help='Learning rate for training.')
    parser.add_argument('-r', '--results_file', type=str, default='results.json', help='File to save results.')
    args = parser.parse_args()

    moduli = args.moduli
    hidden_layer_configs = [tuple(map(int, config.split(','))) for config in args.hidden_layers]
    batch_size = args.batch_size
    epochs = args.epochs
    lr = args.lr
    results_file = args.results_file
    
    # Run the experiments
    run_experiments(moduli, hidden_layer_configs, batch_size, epochs, lr, results_file)
    
    # Print the results
    results = get_results(results_file)
    if results:
        print("Results loaded successfully.")
        plot_results(results)

def single_run_one_hot():
    parser = argparse.ArgumentParser(description="Train and interact with MLP model for modular subtraction, with inputs represented as one-hot vectors.")
    parser.add_argument('-m', '--mod', type=int, default=5, help='Modulus value for single run.')
    parser.add_argument('-hl', '--hidden_layers', type=str, default='4,4', help='Hidden layer sizes as a comma-separated string of integers.')
    parser.add_argument('-b', '--batch_size', type=int, default=32, help='Batch size for training.')
    parser.add_argument('-e', '--epochs', type=int, default=50, help='Number of training epochs.')
    parser.add_argument('-l', '--lr', type=float, default=0.001, help='Learning rate for training.')
    parser.add_argument('-w', '--wd', type=float, default=0, help='Weight decay for training.')
    args = parser.parse_args()

    hidden_layers = tuple(map(int,args.hidden_layers.split(",")))
    train_loader, val_loader, test_loader, train_dataset, val_dataset, test_dataset = load_dataloaders(args.mod, args.batch_size,one_hot=True)

    input_dim = 2*args.mod
    model = MLP(hn_tuple=hidden_layers,num_classes=args.mod,input_dim=input_dim)

    train(model, train_loader, val_loader, epochs=args.epochs, lr=args.lr, wd=args.wd)

    print("Train:\n")
    evaluate(model, train_loader)
    
    print("Test:\n")
    evaluate(model, test_loader)
    t.save(model.state_dict(), f"./models/model_onehot_{args.mod}.pt")

    show_test_examples(model, train_dataset)
    show_test_examples(model, test_dataset)


if __name__ == "__main__":
    create_directories()
    # single_run()
    # experiment()
    single_run_one_hot()