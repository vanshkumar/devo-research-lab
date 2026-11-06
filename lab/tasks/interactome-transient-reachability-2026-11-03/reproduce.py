"""Future authorized reproduction in a NEW task-local output directory.

This script is supplied, statically checked, and NOT executed in this allocation.
It reuses the same scientific declaration and the validated one-sided numerical
driver. It does not overwrite the original consumed artifacts or failed history.
"""
import argparse
import shutil
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    import reference
    import pilot
    import complete_saved
    task=Path(__file__).resolve().parent
    destination=Path(args.output).resolve()
    assert destination.is_relative_to(task) and destination!=task
    assert not destination.exists(),'Choose a new output directory; never erase the prior run'
    destination.mkdir(parents=True)
    for name in ['PROTOCOL.md','CONFIG.json','FREEZE.json','MODEL_REFERENCE.json']:
        shutil.copyfile(task/name,destination/name)
    original_piece=pilot.piece
    def corrected_piece(env,y,start,end,method):
        if method=='literal':
            return complete_saved.literal_piece(env,y,start,end,method)
        return original_piece(env,y,start,end,method)
    pilot.ROOT=destination
    pilot.piece=corrected_piece
    # Fixed source inputs remain read-only in the original task/predecessor.
    pilot.main()

if __name__=='__main__':main()
