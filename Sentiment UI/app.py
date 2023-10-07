from flask import Flask, request, jsonify
import torch
import torch.nn as nn
import re
import pickle

# Load vocab from a pickle file
with open('vocab.pkl', 'rb') as f:
    vocab = pickle.load(f)

app = Flask(__name__)

# Same model architecture
class SentimentClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim):
        super(SentimentClassifier, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.fc = nn.Linear(embedding_dim, 2)

    def forward(self, x):
        x = self.embedding(x)
        x = x.mean(dim=1)
        x = self.fc(x)
        return x

# Same parameters and pre-processing steps
vocab_size = 5000
embedding_dim = 100
max_len = 200

# Loading the model
model = SentimentClassifier(vocab_size, embedding_dim)
model.load_state_dict(torch.load("model.pth", map_location=torch.device('cpu')))
model.eval()

# Preprocessing function
def clean_str(string):
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    return string.strip().lower()

# Tokenizer function
def tokenizer(text):
    return clean_str(text).split()

# Encode function to prepare text
def encode(text, vocab, max_len):
    tokens = tokenizer(text)
    if len(tokens) > max_len:
        tokens = tokens[:max_len]
    return [vocab.get(w, vocab['<UNK>']) for w in tokens] + [vocab['<PAD>']] * (max_len - len(tokens))

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    text = data['text']
    
    # Process and tokenize the text, then convert to Tensor
    input_tensor = torch.tensor([encode(text, vocab, max_len)], dtype=torch.long)
    
    with torch.no_grad():
        output = model(input_tensor)
        _, predicted = torch.max(output.data, 1)
    
    return jsonify({"prediction": int(predicted.item())})

if __name__ == '__main__':
    app.run(debug=True)
