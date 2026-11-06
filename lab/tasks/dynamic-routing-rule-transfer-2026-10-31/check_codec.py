import importlib.util,struct,resource,json
from pathlib import Path
p=Path(__file__).resolve().parent
b=(p/'reward_time.blosc').read_bytes()
print(json.dumps({'header':list(b[:32]),'blosc_header':struct.unpack('<BBBBIII',b[:16]),'modules':{x:bool(importlib.util.find_spec(x)) for x in ['numpy','numcodecs','blosc','blosc2','lz4']},'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))
