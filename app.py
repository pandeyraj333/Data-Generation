import asyncio
import sys
import os
import streamlit as st
import pandas as pd
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv


def run_generate_data_server():
    mcp = FastMCP("Generate")
    @mcp.tool()
    def generate_data(column_names: list, data_types: list, column_types: list, primary_key_col: str, row_count: int) -> list:
        from faker import Faker
        import random
        import csv
        fake = Faker()
        data = []
        # primary_key_col = primary_key[0] if primary_key else None
        primary_key_values = set()

        for i in range(row_count):
            row = {}
            for col, data_type, col_type in zip(column_names, data_types, column_types):
                # Handle primary key
                if col == primary_key_col:
                    pk_val = None
                    while pk_val is None or pk_val in primary_key_values:
                        if data_type == "int":
                            pk_val = fake.unique.random_int()
                        elif data_type == "str":
                            pk_val = fake.unique.uuid4()
                        else:
                            pk_val = fake.unique.random_number(digits=5)
                    primary_key_values.add(pk_val)
                    row[col] = pk_val

                # Data types with optional column_type parameterization
                elif data_type == "int":
                    multiplier = col_type if isinstance(col_type, int) else 1
                    row[col] = fake.random_int(min=1, max=100) * multiplier

                elif data_type == "float":
                    multiplier = col_type if isinstance(col_type, int) else 1
                    row[col] = round((fake.random_number(digits=3) / 10.0) * multiplier, 2)

                elif data_type == "categorical":
                    categories = col_type if isinstance(col_type, list) else ["A", "B", "C"]
                    row[col] = random.choice(categories)

                elif data_type == "str":
                    if col_type == "name":
                        row[col] = fake.name()
                    elif col_type == "email":
                        row[col] = fake.email()
                    elif col_type == "address":
                        row[col] = fake.address()
                    elif col_type == "date":
                        row[col] = fake.date()
                    else:
                        row[col] = fake.word()

                else:
                    row[col] = "N/A"
                
                print(f"Created{i} rows.")

            data.append(row)
            # Write to CSV
        with open("generated_data.csv", mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=column_names)
            writer.writeheader()
            writer.writerows(data)

            
        return "Data generated successfully. Saved as generated_data.py"
    
    
    mcp.run(transport="stdio")

async def run_client(prompt: str) -> str:
    # This subprocess launches the above server
    server_process = await asyncio.create_subprocess_exec(
        sys.executable, "-u", __file__, "server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE
    )

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", __file__, "server"]
    )

    async with stdio_client(server_params, process=server_process) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)

            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
            model = ChatOpenAI(model="gpt-4o",api_key = api_key)
            agent = create_react_agent(model, tools)
            response = await agent.ainvoke({"messages": prompt})
            return response


# Streamlit app

import nest_asyncio
nest_asyncio.apply()

import asyncio

# Call this from streamlit
def run_agent_for_prompt(prompt):
    return asyncio.get_event_loop().run_until_complete(run_client(prompt))


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
                response = run_agent_for_prompt(agent_prompt)

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
