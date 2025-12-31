import re
import pandas as pd
from datetime import datetime
from database.db_utils import get_fund_metadata_df

# -------------------- 1. Load data --------------------
df = get_fund_metadata_df(10)

# -------------------- 2. Extract dependencies --------------------
pattern = re.compile(r'"([^"]+)"!"([^"]+)"!"(current|pf)"')
print('--------------------------------------------------------------------------------------------------------------')
print(datetime.now())
print('--------------------------------------------------------------------------------------------------------------')

def extract_dependencies(formula, fund_id):
    if not isinstance(formula,str):
        return []
    return [(f"{fund_id}!{g}!{k}!{ctx}", ctx) for g,k,ctx in pattern.findall(formula)]

df["dependencies"] = df.apply(lambda row: extract_dependencies(row["formula"], row["fund_id"]), axis=1)

# Build lookup maps
level_map = dict(zip(df["full_key"], df["calculation_level"]))
current_map = dict(zip(df["full_key"], df["is_current"]))
dependency_map = dict(zip(df["full_key"], df["dependencies"]))

# -------------------- 3. Recursive Level Calculation --------------------
memo = {}

def calculate_proper_level(key, dep_map, visited=None):
    if visited is None:
        visited = set()
    
    if key in memo:
        return memo[key]
    
    if key in visited:
        return -1  # Cycle detected
        
    visited.add(key)
    deps = dep_map.get(key, [])
    
    if not deps:
        level = 0
    else:
        # Extract only the key part from (key, ctx) tuples
        dep_keys = [d[0] for d in deps]
        levels = []
        for d_key in dep_keys:
            # If dependency is not in our map, we assume level 0 or handle as missing
            if d_key not in dep_map:
                levels.append(0)
            else:
                l = calculate_proper_level(d_key, dep_map, visited)
                levels.append(l)
        
        if any(l == -1 for l in levels):
            level = -1
        else:
            level = 1 + max(levels) if levels else 0
            
    visited.remove(key)
    memo[key] = level
    return level

df["proper_calculation_level"] = df["full_key"].apply(lambda k: calculate_proper_level(k, dependency_map))

j = 1

for _, row in df.iterrows():
    if row["calculation_level"] != row["proper_calculation_level"]:
        print(j, row['id'], row["full_key"], row["calculation_level"], row["proper_calculation_level"])
        j += 1
        # print("_/\_")

# -------------------- 3.1 Compare Levels --------------------
# level_mismatches = df[df["calculation_level"] != df["proper_calculation_level"]]
# if not level_mismatches.empty:
#     print(f"\nFound {len(level_mismatches)} level mismatches:")
#     print(level_mismatches[["full_key", "calculation_level", "proper_calculation_level"]].head(20))
# else:
#     print("\n✅ All calculation levels match the proper hierarchical levels.")

# -------------------- 4. Validate --------------------
violations = []

i = 1

def print_msg(this_key, error_type, dep_key, dep_ctx, dep_level, this_level, this_fund_id, this_datagroup_id, this_key_id, this_proper_level):
    global i
    if "Pipeline Transactions" in dep_key:
        return
    print(f"{i}. [{this_fund_id}][{this_datagroup_id}][{this_key_id}] {this_key} [level {this_level}]-> {error_type} -> {dep_key} [level {dep_level}] -> [proper level {this_proper_level}]")
    i += 1



for _, row in df.iterrows():
    this_key = row["full_key"]
    this_fund_id = row["fund_id"]
    this_datagroup_id = row["datagroup_id"]
    this_key_id = row["id"]
    this_level = row["calculation_level"]
    this_is_current = row["is_current"]
    this_formula = row["formula"]
    this_proper_level = row["proper_calculation_level"]
    this_ctx = "current" if this_is_current else "pf"

    for dep_key, dep_ctx in row["dependencies"]:
        dep_level = level_map.get(dep_key)
        dep_is_current = current_map.get(dep_key)
        dep_ctx = "current" if dep_is_current else "pf"

        if this_level != 0 and this_formula is None:
            violations.append({
                "key": this_key,
                "problem": "Invalid calculation order",
                "dependency": dep_key,
                "dependency_level": dep_level,
                "key_level": this_level
            })
            print_msg(this_key, "Invalid calculation order", dep_key, dep_ctx, dep_level, this_level, this_fund_id, this_datagroup_id, this_key_id, this_proper_level)
            continue

        # Missing key
        if dep_level is None:
            violations.append({
                "key": this_key,
                "problem": "Missing dependency",
                "dependency": dep_key,
                "context": dep_ctx
            })
            print_msg(this_key, "Missing dependency", dep_key, dep_ctx, dep_level, this_level, this_fund_id, this_datagroup_id, this_key_id, this_proper_level)
            continue

        # Calculation order check
        if dep_level >= this_level and this_level != 0:
            violations.append({
                "key": this_key,
                "problem": "Invalid calculation order",
                "dependency": dep_key,
                "dependency_level": dep_level,
                "key_level": this_level
            })
            print_msg(this_key, "Invalid calculation order (2)", dep_key, dep_ctx, dep_level, this_level, this_fund_id, this_datagroup_id, this_key_id, this_proper_level)
            continue

        # Context correctness check
        if dep_ctx == "current" and dep_is_current is not True:
            violations.append({
                "key": this_key,
                "problem": "Expected current but dependency is pf",
                "dependency": dep_key,
                "dependency_is_current": dep_is_current
            })
            print_msg(this_key, "Expected current but dependency is pf", dep_key, dep_ctx, dep_level, this_level, this_fund_id, this_datagroup_id, this_key_id, this_proper_level)
            continue

        if dep_ctx == "pf" and dep_is_current is not False:
            violations.append({
                "key": this_key,
                "problem": "Expected pf but dependency is current",
                "dependency": dep_key,
                "dependency_is_current": dep_is_current
            })
            print_msg(this_key, "Expected pf but dependency is current", dep_key, dep_ctx, dep_level, this_level, this_fund_id, this_datagroup_id, this_key_id, this_proper_level)
            continue

# -------------------- 4. Report --------------------
violations_df = pd.DataFrame(violations)

if violations_df.empty:
    print("✅ All calculation levels and contexts are valid.")