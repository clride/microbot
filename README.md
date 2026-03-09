# Microbot: tiny LLM
Microbot is a tiny agentic AI tool that can run with Openrouter and OpenAI. It has access to simple commands so it can do everything it needs to
without complications while being easy to observe and monitor. It has no internet access and a restricted python runtime (though not sandboxed). The entire implementation
sits at a few hundred lines of code.

## How to use
- Ideally set up an LXC or Docker Container
- Install the pip requirements: ```pip install -r pip.txt```
- Choose a model provider in ```agent_config.py```
- Paste your API Token into a ```.env``` file: ```API_KEY=YOUR_KEY_HERE```
- Run the program with ```python3 main.py```
- Chat with microbot, observe how it interacts with your system and runs commands.
