import argparse
from pathlib import Path
import os

parser = argparse.ArgumentParser()
# Compare between two provided schema file
parser.add_argument("schema1", type=Path)
parser.add_argument("schema2", type=Path)
args = parser.parse_args()

# Read schema file
schema1 = args.schema1.read_text()
schema2 = args.schema2.read_text()

# Clean up schema file
schema1 = schema1.rstrip()
schema2 = schema2.rstrip()

# Compare
get_current = os.environ.get("GITHUB_OUTPUT", "")
if schema1 == schema2:
    print("Schema are the same")
    # Set exit code to 0 in GITHUB_OUTPUT
    os.environ["GITHUB_OUTPUT"] = get_current + "SUCCESS=1"
else:
    print("Schema are different")
    # Find the first difference
    for i, (line1, line2) in enumerate(zip(schema1.splitlines(), schema2.splitlines())):
        if line1 != line2:
            print(f"First difference at line {i}")
            print(f"Schema 1: {line1}")
            print(f"Schema 2: {line2}")
            break
    os.environ["GITHUB_OUTPUT"] = get_current + "SUCCESS=0"
