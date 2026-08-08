import json, os
_DIR = os.path.dirname(__file__)
DATA = json.load(open(os.path.join(_DIR, 'data.json')))
RULES_RAW = json.load(open(os.path.join(_DIR, 'rules_raw.json')))
SECTION_INDEX = json.load(open(os.path.join(_DIR, 'section_index.json')))
