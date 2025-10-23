# LLM Website - Chat Interface

A beautiful, minimalist chat interface with multiple chat tiles that can communicate with a Python backend.

## Features

- 🎨 Google-inspired minimalist design with soft gradient colors
- 💬 Multiple independent chat tiles
- 🤖 Automatic assistant responses via Python backend
- 🎯 Manual role toggle to simulate both sides of conversation
- 🖱️ Draggable chat tiles
- ✨ Smooth animations and modern UI

## Setup

### 1. Install Python Dependencies

```bash
python mock_assistant.py
```

### 2. Start the Python Backend

```bash
python mock_assistant.py
```

The server will start on `http://localhost:5001`

### 3. Open the HTML File

Simply open `index.html` in your web browser.

## Usage

1. **Create a Chat Tile**: Click the blue `+` button on the right side
2. **Send Messages**: 
   - Type a message and press Enter or click Send
   - When in "User" mode, the assistant will automatically respond
   - Switch to "Assistant" mode to manually type assistant responses
3. **Drag Tiles**: Click and drag the tile header to reposition
4. **Multiple Chats**: Create as many chat tiles as you need!

## Architecture

- **Frontend**: Single-page HTML with vanilla JavaScript
- **Backend**: Flask server (`mock_assistant.py`)
  - `/chat` endpoint: POST requests with user messages
  - `mock_reply()` function: Returns responses (currently returns "mock response")

## Customizing Responses

To change the assistant's behavior, edit the `mock_reply()` function in `mock_assistant.py`:

```python
def mock_reply():
    return "Your custom response here"
```

You can make it more sophisticated by accepting the user message as a parameter and returning different responses based on the input.

## Testing the API Directly

```bash
curl -X POST http://localhost:5001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

Expected response:
```json
{"response": "mock response"}
```

## Troubleshooting

### HTTP ERROR 403 / Access Denied

If you see "Access to localhost was denied" or HTTP ERROR 403:

1. **Make sure the Flask server is running**:
   ```bash
   python3 mock_assistant.py
   ```
   You should see:
   ```
   🚀 Mock Assistant Server Starting...
   📡 Server running on http://localhost:5001
   ```

2. **Try the startup script** (Mac/Linux):
   ```bash
   chmod +x start_server.sh
   ./start_server.sh
   ```

3. **Check if the port is accessible**:
   ```bash
   curl http://localhost:5001/health
   ```
   Should return: `{"status":"ok"}`

4. **Browser Security**: Open `index.html` by:
   - Double-clicking the file (opens in default browser)
   - Or use a local web server:
     ```bash
     python3 -m http.server 8080
     ```
     Then visit: http://localhost:8080/index.html

### Other Common Issues

- **Error: "Could not connect to assistant"**: Make sure `mock_assistant.py` is running on port 5001
- **CORS errors**: The Flask server has CORS enabled. The HTML will try both `localhost` and `127.0.0.1` automatically
- **Port already in use**: Change the port in `mock_assistant.py` (line with `app.run()`) and update the URLs in `index.html`
- **Dependencies missing**: Run `pip3 install -r requirements.txt`
- **"Method Not Allowed" error**: This usually means you're accessing `/chat` with GET instead of POST. Use the web interface or curl with POST method.

