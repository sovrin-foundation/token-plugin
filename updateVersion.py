import sys
import json

with open('sovtoken/sovtoken/metadata.json', 'r') as f:
    data = json.load(f)
    data["version"] = sys.argv[1]
    json.dump(data, open("sovtoken/sovtoken/metadata.json", "w"), indent=2)

with open('sovtokenfees/sovtokenfees/metadata.json', 'r') as f:
    data = json.load(f)
    data["version"] = sys.argv[1]
    json.dump(data, open("sovtokenfees/sovtokenfees/metadata.json", "w"), indent=2)

print("Updated version of sovtoken and sovtokenfees metadata.json to: ", sys.argv[1])
