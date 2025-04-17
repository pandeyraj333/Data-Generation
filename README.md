# Data-Generation
Using AI agent and mcp to generate data.
# 🤖 Data-Generation with AI Agent + MCP

This project demonstrates how to generate realistic synthetic data using an AI agent powered by the **Multi-Agent Communication Protocol (MCP)**. The app is built with **Streamlit** for an interactive front-end experience.

## 🚀 Overview

The system uses a custom AI agent that:
- Understands user prompts describing the desired data.
- Infers the schema (columns, data types, primary key).
- Generates realistic dummy data using [Faker](https://faker.readthedocs.io/) or similar libraries.
- Returns a structured dataset based on prompt inputs.

This is especially useful for testing, prototyping, and demonstrations where real data isn't available.

## 🧠 Powered By

- **Python**
- **Fast MCP** - for modular multi-agent communication and reasoning.
- **Faker** - to generate fake but realistic values (e.g., names, emails, locations).
- **Streamlit** - for the web interface.

## 🖥️ How It Works

1. User enters a natural language prompt describing the data (e.g., "Generate customer data with name, email, and purchase history").
2. The AI agent:
   - Parses the prompt.
   - Defines a schema.
   - Infers the data types and relationships.
3. A synthetic dataset is created and displayed in a Streamlit app.

