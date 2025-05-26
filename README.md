# AIM-OS (Artificial Intelligence Manager - Operating Systems)

This project integrates capturing information from a Linux computer, and sends it to a LLM for analysis through a terminal. It is ideal for applications that need to interact with computers and leverage natural language processing.

## Features

- **Data Capture**: Extracts real-time information from the computer using Rust and Bash.
- **Integration with AI**: Analyzes and responds using the captured data with an LLM.

## Prerequisites

### For Linux:
- Rust
- Python

Additionally, the following Python libraries are required:
- rich
- openai

## Installation

Clone the repository to your local machine:

```bash
git clone https://github.com/DCV05/AIM-OS.git
```

Navigate to the project directory and install the Python dependencies:

```bash
cd AIM-OS
pip install -r requirements.txt
```

# Configuration

Set up the necessary keys for the OpenAI API in a .env file in the root of the project:

```bash
OPENAI_API_KEY='your_api_key_here'
```

# Usage

## Terminal Interface

To run the terminal interface, use the following command:

```bash
python main.py -t
```
