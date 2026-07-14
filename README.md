# Smart
SMART - Systematic Mortgage Analysis with Responsible Thinking. 
An Canada-specific agent that specializes in mortgage calculations with considerations of responsible personal finance.

# Reference
- A significant amount of `ResponsesAgent`, `AgentServer` and Lakebase memory boiler-plate codes are referenced from Databricks [reference](https://github.com/databricks/app-templates/tree/main/agent-langgraph-advanced)

# Setup
- Install conda environment: `conda env create -f conda.yml`
- Activate conda environment: `conda activate smart`
- Install project package: `pip install .` or `pip install -e .` for editable installation

# Start the Program
From the root folder
- Use makefile:
    - server: `make server`
    - client: `make client`
- Direct execution
    - server: `python agent_server/start_server.py`
    - client: `python client/client.py`

