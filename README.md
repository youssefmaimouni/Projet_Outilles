# Transportation Network Optimization System

![Network Optimization Demo](https://via.placeholder.com/1200x600?text=Transportation+Network+Visualization)

A complete web-based solution for modeling and optimizing transportation networks using graph algorithms, built with Flask and NetworkX.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Algorithms Implemented](#algorithms-implemented)
- [Dependencies](#dependencies)
- [Configuration](#configuration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

### Core Functionality
- 🚛 **Network Modeling**
  - Create custom transportation networks
  - Define nodes (cities, warehouses)
  - Configure routes with capacity, cost, and time parameters

- ⚡ **Optimization Algorithms**
  - Maximum Flow (Ford-Fulkerson)
  - Minimum Cost Flow
  - Shortest Path (Dijkstra)
  - Edmonds-Karp variant
  - Push-Relabel implementation

- 📊 **Visualization Tools**
  - Interactive network graphs
  - Color-coded edge utilization
  - Flow/capacity indicators
  - Optimal path highlighting

### Advanced Features
- 📈 Performance metrics
- 💰 Cost analysis breakdown
- 🛣️ Multiple path identification
- 🔄 Dynamic graph updates

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/youssefmaimouni/projet_outilles.git
   cd projet_outilles

## Quick Start

2. Install dependencies from `requirements.txt`:
    ```bash
    pip install -r requirements.txt

3. Run the application using `app.py`
    ```bash
    python app.py 

4. Access the web interface at `http://localhost:5000`

## Project Structure
```markdown
    projet_outilles/
    ├── app.py                # Main application logic
    ├── templates/            # HTML templates
    │   ├── index.html        # Landing page
    │   ├── form.html         # Network configuration form
    │   └── results.html      # Optimization results
    ├── static/               # Static files (CSS, JS)
    ├── requirements.txt      # Dependencies
    └── README.md             # This file