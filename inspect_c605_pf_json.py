import json
from pathlib import Path
from pprint import pprint

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\StreamingAssets\WangsukDXF\ParsedUnityJson_C605\c605_pf_hpile.json")
data = json.loads(path.read_text(encoding="utf-8"))

print("type:", type(data))

if isinstance(data, dict):
    print("root keys:", list(data.keys()))
    for k, v in data.items():
        if isinstance(v, list):
            print("list key:", k, "count:", len(v))
            if len(v) > 0:
                print("first item:")
                pprint(v[0], width=160)
                print("second item:")
                pprint(v[1], width=160)
            break

elif isinstance(data, list):
    print("list count:", len(data))
    if len(data) > 0:
        print("first item:")
        pprint(data[0], width=160)
        print("second item:")
        pprint(data[1], width=160)
