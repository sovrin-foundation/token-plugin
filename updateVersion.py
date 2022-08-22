import argparse
import json
import time
import semver

ap = argparse.ArgumentParser("Updates Version in json")

ap.add_argument("-t", "--tag", help="Version to be set to",)
args = vars(ap.parse_args())


def updateWithTag(ver):
    if not semver.VersionInfo.isvalid(ver):
        raise ValueError('No Valid Semver in Tag')
    return ver


def updateWithTimestamp():
    uxtimestamp = str(int(time.time()))
    version = "str"
    with open('sovtoken/sovtoken/metadata.json', 'r') as f:
        data = json.load(f)
        v = semver.VersionInfo.parse(data["version"])
        print(v)
        v = v.replace(prerelease="dev" + uxtimestamp)
        print(v)
        version = str(v)
    return version


version = "string"

if args['tag'] is not None:
    version = updateWithTag(args['tag'])
    print("Version will be updated to: " + version)
else:
    version = updateWithTimestamp()
    print("Replacing  Dev-Version with UX-timestamp: " + version)

with open('sovtoken/sovtoken/metadata.json', 'r') as f:
    data = json.load(f)
    data["version"] = version
    json.dump(data, open("sovtoken/sovtoken/metadata.json", "w"), indent=2)

with open('sovtokenfees/sovtokenfees/metadata.json', 'r') as f:
    data = json.load(f)
    data["version"] = version
    json.dump(data, open("sovtokenfees/sovtokenfees/metadata.json", "w"), indent=2)

print("Updated version of sovtoken and sovtokenfees metadata.json to: ", version)
