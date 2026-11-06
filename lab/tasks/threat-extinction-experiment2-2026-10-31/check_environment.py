import importlib.util
print({m: importlib.util.find_spec(m) is not None for m in ['numpy', 'scipy', 'pandas', 'pyreadstat']})
