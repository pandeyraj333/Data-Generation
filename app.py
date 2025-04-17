# app.py
import asyncio
import os
import streamlit as st
import pandas as pd

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# Set your OpenAI API Key securely (move to .env or secrets in production)
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Setup model
model = ChatOpenAI(model="gpt-4o",api_key = api_key)

# Server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",
    args=["generate_data_server.py"],  # <-- This must exist in your project root
)

# Async function to interact with agent
async def run_agent(prompt: str) -> str:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)

            agent = create_react_agent(model, tools)
            result = await agent.ainvoke({"messages": prompt})
            return result

# Streamlit app
st.title("🧠 AI Data Generator with MCP")
st.markdown("Enter a prompt to generate synthetic data using an AI agent.")

user_input = st.text_area("📝 Your Prompt", placeholder="E.g., Generate a dataset with 600 rows about employee names, their salary, and their id.")

if st.button("Generate Data"):
    if user_input:
        with st.spinner("Running AI agent..."):
            agent_prompt = f'''
            You are a data generation assistant that creates structured dummy datasets based on a user's description using the generate_data() function.

            The user will describe the dataset they need. Your job is to:

            Parse the user's description to extract:

            The column names

            The data type of each column (int, float, str, categorical)

            A column type for each:

            For int and float, this is a numeric multiplier (e.g., 1 for small values like age, 100 or 1000 for values like revenue).

            For categorical, it is a list of categories (e.g., ["Male", "Female"], ["Low", "Medium", "High"]).

            For str, this is the semantic type (e.g., name, email, address, date, or leave blank for generic string).

            Which column(s) are primary keys

            The number of rows the user wants to generate

            Use this structured information to call the function provided to you.

            🧠 Examples of Interpretation:
            If a user says: "I need 100 rows of customer data with id, name, email, age, and purchase amount. Id should be unique. Age should be realistic, and purchase amount should be in hundreds."

            Column Names: ["id", "name", "email", "age", "purchase"]

            Data Types: ["int", "str", "str", "int", "float"]

            Column Types: [None, "name", "email", 1, 100]

            Primary Key: "id"

            Row Count: 100

            If a user says: "Generate 50 products with unique product codes, a category (Electronics, Apparel), and a price in thousands."

            Column Names: ["product_code", "category", "price"]

            Data Types: ["str", "categorical", "float"]

            Column Types: ["uuid", ["Electronics", "Apparel"], 1000]

            Primary Key: "product_code"

            Row Count: 50

            📌 Important Instructions:
            Be sure to extract column types correctly — don't assume default multipliers or categories if the user provides specific ones.

            If no primary key is specified, assume an appropriate key, if none seem right leave an empty string.

            If any details are ambiguous or missing, make a reasonable assumptions.

            After generating the data, saving it in a csv.

            Here is the user request:
            {user_input}
            '''
            try:
                response = asyncio.run(run_agent(agent_prompt))

                # Assume agent's response contains CSV string
                # csv_data = response.strip()

                # Save to CSV
                # with open("generated_data.csv", "w", newline='', encoding='utf-8') as f:
                #     f.write(csv_data)

                # Display as table
                df = pd.read_csv("generated_data.csv")
                csv_data = df.to_csv(index=False)
                st.success("Dataset generated successfully!")
                st.download_button("⬇️ Download CSV", csv_data, "generated_data.csv", "text/csv")
                st.dataframe(df)

            except Exception as e:
                st.error(f"❌ Error: {e}")
    else:
        st.warning("Please enter a prompt.")
