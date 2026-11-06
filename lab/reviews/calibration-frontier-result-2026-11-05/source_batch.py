"""Score a finite batch of completed immutable source chunks exactly once."""
import sys
import numpy as np
from independent import HERE, MAIN, Accounting, save, score


def main():
    upto=int(sys.argv[1])
    meter=Accounting('early independent completed-source batch up to '+str(upto))
    records=meter.json(MAIN/'MAIN_SOURCE_DRAWS.json')['draws']
    assert len(records)>=upto
    cache=meter.arrays(HERE/'FIXED_CACHE.npz',keys=['subjects','observed'])
    out=HERE/'source_independent'
    out.mkdir(exist_ok=True)
    completed=[]
    for draw in range(upto):
        if (out/f'draw_{draw:02d}.npz').exists(): continue
        data=meter.arrays(MAIN/f'source_chunks/draw_{draw:02d}.npz',keys=['samples','subjects','names','cutoffs','windows'])
        assert np.array_equal(data['subjects'],cache['subjects'])
        assert data['names'].tolist()==['growth','recent_growth']
        assert data['samples'].shape==(64,2,2,256,2,7)
        metrics=np.empty((64,2,2,2,8));halves=np.empty((64,2,2,2,2))
        for i in range(64):
            for c in range(2):
                for actor in range(2):
                    for w,horizon in enumerate([500,2000]):
                        metrics[i,c,actor,w]=score(data['samples'][i,c,actor,:,w],cache['observed'][i,w],horizon)
                    for half in range(2):
                        halves[i,c,actor,half]=score(data['samples'][i,c,actor,half*128:(half+1)*128,1],cache['observed'][i,1],2000)[:2]
        np.savez_compressed(out/f'draw_{draw:02d}.npz',metrics=metrics,halves=halves,
                            subjects=cache['subjects'],input_sha256=np.array(meter.reads[-1]['sha256']))
        completed.append(draw)
    save(f'SOURCE_BATCH_{upto:02d}_RESOURCES.json',meter.receipt())
    print(dict(completed=completed,resources=meter.receipt(),note='partial reconstruction only, no terminal source-family inference'))


if __name__=='__main__': main()
