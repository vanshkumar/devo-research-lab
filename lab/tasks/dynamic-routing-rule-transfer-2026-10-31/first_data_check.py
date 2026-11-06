"""Offline source check of ONE reward vector, not a transfer assay.

The stored Blosc1 frame uses LZ4, byte shuffle, one block, eight splits.
This small decoder only supports that checked framing; no general loader.
"""
import csv,hashlib,json,math,resource,struct,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def lz4_block(src):
    dst=bytearray(); i=0
    while i<len(src):
        token=src[i]; i+=1
        n=token>>4
        if n==15:
            while True:
                x=src[i]; i+=1; n+=x
                if x!=255: break
        dst.extend(src[i:i+n]); i+=n
        if i==len(src): break
        off=int.from_bytes(src[i:i+2],'little'); i+=2
        assert 0<off<=len(dst)
        n=token&15
        if n==15:
            while True:
                x=src[i]; i+=1; n+=x
                if x!=255: break
        for _ in range(n+4): dst.append(dst[-off])
    assert i==len(src)
    return bytes(dst)

def decode_stored_frame(b):
    version,codecversion,flags,typesize,nbytes,blocksize,cbytes=struct.unpack('<BBBBIII',b[:16])
    assert (version,codecversion,flags,typesize,nbytes,blocksize,cbytes)==(2,1,33,8,4304,4304,len(b))
    start=struct.unpack('<I',b[16:20])[0]; assert start==20
    pos=start; splits=[]
    for k in range(8):
        clen=struct.unpack('<I',b[pos:pos+4])[0]; pos+=4
        payload=b[pos:pos+clen]; pos+=clen
        decoded=payload if clen==538 else lz4_block(payload)
        assert len(decoded)==538
        splits.append(decoded)
    assert pos==len(b)
    out=bytes(splits[j][i] for i in range(538) for j in range(8))
    assert len(out)==nbytes
    return out

b=(ROOT/'reward_time.blosc').read_bytes()
raw=decode_stored_frame(b)
values=struct.unpack('<538d',raw)
finite=[(i,x) for i,x in enumerate(values) if math.isfinite(x)]
diffs=[finite[k][1]-finite[k-1][1] for k in range(1,len(finite))]
meta_b=(ROOT/'nwb_metadata.json').read_bytes(); meta=json.loads(meta_b)['metadata']
shape=meta['intervals/trials/reward_time/.zarray']['shape']; assert shape==[len(values)]
assert all(math.isnan(x) or math.isfinite(x) for x in values)
with (ROOT/'reward_times.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['trial_position_0based','reward_time_seconds']);w.writerows(enumerate(values))
result={
    'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
    'kind':'actual bounded source-vector calculation; NOT full source certification or forecast test',
    'session_from_object_path':'742903_2024-10-22',
    'subject_from_object_path':'742903; scalar subject value not acquired',
    'rows':len(values),'finite_reward_times':len(finite),
    'nan_reward_times':sum(math.isnan(x) for x in values),
    'reward_times_strictly_increasing':all(x>0 for x in diffs),
    'minimum_finite_interreward_seconds':min(diffs),
    'maximum_finite_interreward_seconds':max(diffs),
    'first_five_finite_reward_trial_time_pairs':finite[:5],
    'last_five_finite_reward_trial_time_pairs':finite[-5:],
    'schema_columns':len(meta['intervals/trials/.zattrs']['colnames']),
    'schema_has_distinct_scheduled_and_delivered_reward_flags':all('intervals/trials/'+x+'/.zarray' in meta for x in ['is_reward_scheduled','is_noncontingent_reward','is_contingent_reward']),
    'schema_has_instruction_flag': 'intervals/trials/is_instruction/.zarray' in meta,
    'source_frame_sha256':hashlib.sha256(b).hexdigest(),
    'decoded_sha256':hashlib.sha256(raw).hexdigest(),
    'codec_validation':'header, 8 split lengths, complete frame consumption, declared dtype/shape and finite/NaN checks; independent codec replay UNRUN',
    'certified':False,
    'missing_actual_values':['stim_name','is_response','stim_start_time','response_window_start_time','response_window_stop_time','response_time','block_index','is_instruction','is_reward_scheduled','is_noncontingent_reward','is_contingent_reward','is_opto','is_repeat'],
    'first_encounter_opportunity_count':None,
    'unrun':['full chronology join','task-script deployment provenance','license certification','independent-animal split','scientific model freeze','recovery/null controls','held-animal forecasts/scoring','independent scientific review'],
    'scientific_interpretation':'Cannot test cross-stimulus transfer from a reward-time vector alone. Missing acquired columns are not absent source columns.',
    'measured_process_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'conservative_read_decode_hash_charge_bytes':3*len(meta_b)+4*len(b)+4*len(raw)
}
(ROOT/'FIRST_DATA_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
