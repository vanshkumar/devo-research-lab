"""Single amended original-configuration-scale affordability run."""
from pathlib import Path
import traceback
from feasibility import run

if __name__ == '__main__':
    try:
        run(N=1000000, prefix='FULL_')
    except BaseException:
        (Path(__file__).resolve().parent / 'FULL_FEASIBILITY_FAILURE.txt').write_text(traceback.format_exc())
        raise
