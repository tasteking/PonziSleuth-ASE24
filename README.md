# PonziSleuth

[![DOI](https://zenodo.org/badge/805785233.svg)](https://zenodo.org/doi/10.5281/zenodo.13326751)

Official code for "SemanticSleuth: Identifying Ponzi Contracts via Large Language Models" which has been accepted by ASE 2024.

For ease of use, we have made some changes to the original implementation in the paper.

## Usage

### Linux

**Clone the repo, change directory to the root of the repo directory and run:**

- Optionally, create a virtual environment
    ```bash
    # if you have not installed Anaconda, install it first
    # wget https://repo.anaconda.com/archive/Anaconda3-2023.03-0-Linux-x86_64.sh
    # bash Anaconda3-2023.03-0-Linux-x86_64.sh

    conda create -n PonziSleuth python=3.10.14
    conda activate PonziSleuth
    ```

    If you use other vitural environment managers, make sure that the python version of the virtural environment is `>=3.10.14`

- Install PonziSleuth python package
    ```bash
    python3 -m pip install -e .
    ```

- Setting environment variables

    To use the services of openai and etherscan, provide your own api key as environment variables:
    ```bash
    export OPENAI_API_KEY=your key
    export ETHERSCAN_API_KEY=your key
    ```

- In a new terminal, install Ollama and pull models

    Use Ollama to interact with open source LLMs
    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```

    Run Ollama serve
    ```bash
    ollama serve
    ```

    Pull model from Ollama server in another terminal
    ```bash
    ollama pull llama3
    ```

- Go back to the terminal with environment variables of the api key, run the test

    Everthing prepared right now, run a small test:
    ```bash
    bash test/test.sh
    ```
    
- If the test doesn't go wrong, detection result will output to `result` directory and the following command should work: 
    ```bash
    # help
    PonziSleuth --help

    # usage
    PonziSleuth -p(-f) /path/to/file(/filename) -m model -t temperature
    ```
    
**Then try this tool as your wish**