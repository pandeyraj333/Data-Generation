# generate_data_server.py
from mcp.server.fastmcp import FastMCP

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

        
    return data

if __name__ == "__main__":
    mcp.run(transport="stdio")
