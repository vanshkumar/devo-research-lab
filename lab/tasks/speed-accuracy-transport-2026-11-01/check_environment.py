import importlib.util
import sys
print(sys.version)
print({p:bool(importlib.util.find_spec(p)) for p in ['numpy','pandas','scipy','pyreadr','rdata']})
