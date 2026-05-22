import sys
import pandas as pd

print("arguments", sys.argv)

df = pd.DataFrame({"A": [1,2], "B": [3,4]})
print(df.head())

df.to_parquet(f"output_{sys.argv[1]}.parquet")

month = int(sys.argv[1])
print(f"running pipline for month {month}")