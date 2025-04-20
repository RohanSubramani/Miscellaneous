# Dependency Education System

This folder contains code to have LLMs provide detailed knowledge graphs to teach users about any subject of their choosing. The rest of this readme is written by Claude.

## Features

- **Interactive Graph Visualization**: Dynamic, force-directed graph layout showing concept dependencies
- **LaTeX Support**: Full LaTeX support for mathematical notation in both concept titles and explanations
- **Multiple Graph Management**: Create and switch between different knowledge graphs
- **Bidirectional Navigation**: Navigate both dependencies and dependent concepts
- **Real-time Updates**: Automatic updates when content changes
- **Cycle Prevention**: Built-in detection and prevention of circular dependencies

## Components

- `education_agent.py`: Main Python backend handling graph management and LLM interactions
- `graph.html`: Interactive web interface for visualizing and navigating the knowledge graph
- `graph_style.css`: Styling for the web interface with a modern, dark theme

## Setup

1. Install required Python packages:
   ```bash
   pip install openai
   ```

2. Set up your OpenAI API key:
   ```bash
   export OPENAI_API_KEY='your-api-key'
   ```

3. Configure your desired OpenAI model:
   - Open `education_agent.py`
   - Find the line `GLOBAL_MODEL = "gpt-4.1-mini"`
   - Change it to your preferred model (e.g., "gpt-4.1")

4. Start the web interface server (the HTML must be accessed through a web server, not opened directly):
   ```bash
   # Using Python's built-in server
   python -m http.server
   # Then visit http://localhost:8000/graph.html in your browser
   
   # Or using any other web server of your choice
   ```

5. In a new terminal, run the education agent:
   ```bash
   python education_agent.py
   ```

6. Interact with the education agent:
   - First, you'll be prompted to select a graph or create a new one
   - For a new graph, enter a descriptive name (e.g., "linear_algebra" or "python_basics")
   - Then, start asking questions or giving commands about what you want to learn
   - Example prompts:
     ```
     "Explain the concept of derivatives in calculus"
     "Create a node about Python lists with their basic operations"
     "Add sorting algorithms as a concept and connect it to its prerequisites"
     ```
   - Type 'end' to exit the program

## Usage

### Creating and Managing Graphs

1. When you start the system, you'll be prompted to either:
   - Select an existing graph
   - Create a new graph

2. Enter your queries to create or modify concepts. The system will:
   - Create new concepts with explanations
   - Establish dependencies between concepts
   - Prevent circular dependencies
   - Update the visualization in real-time

### Web Interface

The web interface (`graph.html`) provides:

- Interactive graph visualization
- Concept details panel showing:
  - Full explanation with LaTeX support
  - List of dependencies
  - List of concepts that depend on this concept
- Graph selection dropdown
- Real-time updates

### LaTeX Support

Use LaTeX notation in both titles and explanations:
- Inline math: `$...$` or `\(...\)`
- Display math: `$$...$$` or `\[...\]`

### File Structure

```
dependency_education/
├── education_agent.py    # Main backend system
├── graph.html           # Web visualization interface
├── graph_style.css      # Styling for the interface
├── graphs/             # Directory containing graph data
│   ├── available_graphs.json   # List of available graphs
│   └── [graph_name].json      # Individual graph data
└── README.md           # This documentation
```

## Technical Details

### Graph Data Structure

Each node in the graph contains:
- Title (supports LaTeX)
- Detailed explanation (supports LaTeX)
- List of dependencies
- List of concepts that depend on this concept ("relevant for")

### Visualization Features

- Force-directed layout with hierarchical organization
- Color coding for nodes:
  - Blue: Concepts with explanations
  - Gray: Concepts without explanations
- Interactive node selection and focus
- Smooth animations for transitions
- Responsive design