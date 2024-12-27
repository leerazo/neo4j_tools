# Neo4j Aura Demo Manager

This repository is intended to help streamline Neo4j Aura deployment and data loading for the purposes of quickly and smoothly creating cloud demos. 

## Install Environment

In order to make use of these procedures, you will need to have an Aura account created either through a cloud marketplace or directly from Neo4j. You will also need to create an API key in your Aura account. The documents from links below will guide you through the process of setting this up.

Everything here is still in "beta" and may not work correctly. The core python script(s) are available in [this folder](scripts)

First let's setup python and install the needed libraries.

Let's install python & pip first:

    apt install -y python
    apt install -y pip

Now, let's create a Virtual Environment to isolate our Python environment and activate it

    apt-get install -y python3-venv
    python3 -m venv /app/venv/aura-api
    source /app/venv/aura-api/bin/activate

To install dependencies:

    pip install -r requirements.txt

## Setup Neo4j Aura API Access 

Next, follow the links below to setup API access to Aura
- [Instructions for setting up your Aura API key](01-setup_aura_api/)
- [Authenticating and exploring the Aura environment (Notebook)](02-using_aura_api/)
- [Deploying Aura and loading data](03-deploying_aura)
