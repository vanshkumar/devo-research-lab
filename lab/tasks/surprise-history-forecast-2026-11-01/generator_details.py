import pathlib
p=pathlib.Path(__file__).resolve().parent
lines=(p/'task_generate.source').read_text().splitlines()
for i in range(75,183):print(i+1,lines[i])
