"""Named official source-only check; no experimental files, auth, or outputs."""
from common import *
import urllib.request,urllib.error,re

RIG='67f80a964dd5c05751e415ef9d08b52bf03cfb46' # official3.7.4 tag already cached
RAW='https://raw.githubusercontent.com/int-brain-lab/'
API='https://api.github.com/repos/int-brain-lab/ibllib/commits?path=ibllib%2Fio%2Fextractors%2Ftraining_trials.py&until=2023-12-20T09%3A08%3A38Z&per_page=1'
DOC='https://docs.internationalbrainlab.org/notebooks_external/loading_trials_data.html'
OUT=HERE/'official_source';OUT.mkdir(exist_ok=True)
LOG=HERE/'OFFICIAL_SOURCE_REQUESTS.jsonl'
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None

def main():
    prior=[json.loads(l) for l in read(LOG).splitlines()] if LOG.exists() else []
    spent=sum(r['received_bytes'] for r in prior);all_requests=prior.copy()
    opener=urllib.request.build_opener(NoRedirect)
    def request(url,name,limit):
        nonlocal spent
        p=OUT/name
        assert url.startswith(RAW) or url==API or url==DOC
        previous=next((r for r in prior if r['url']==url and r['success']),None)
        if previous:return read(p,previous['sha256'])
        assert spent+limit<=5000000 and 458383178+spent+limit<=500000000
        b=bytearray();r=dict(utc=utc(),url=url,local=str(p.relative_to(HERE)),method='GET',public_anonymous=True,
            response_limit_bytes=limit,success=False)
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'ibl-contrast-field-source-check/1.0','Accept-Encoding':'identity'})
            with opener.open(req,timeout=25) as f:
                assert f.status==200 and f.url==url
                n=f.headers.get('Content-Length');assert n is None or int(n)<=limit
                r.update(status=f.status,content_type=f.headers.get('Content-Type'),etag=f.headers.get('ETag'))
                while len(b)<limit:
                    v=f.read(min(65536,limit-len(b)))
                    if not v:break
                    b.extend(v)
                assert len(b)<limit or (n is not None and int(n)==len(b)), 'response reached declared boundary'
                assert n is None or int(n)==len(b)
            p.write_bytes(b);r.update(success=True,sha256=hashlib.sha256(b).hexdigest())
            return bytes(b)
        except Exception as exc:
            r['error']=repr(exc)
            if b:p.with_suffix(p.suffix+'.partial').write_bytes(b)
            return None
        finally:
            r['received_bytes']=len(b);spent+=len(b);all_requests.append(r)
            with LOG.open('a') as f:f.write(json.dumps(r)+'\n')
            print(name,r['success'],len(b),r.get('error',''),flush=True)
    # The date bounds a relevant official version; does not certify the S3 ETL commit.
    b=request(API,'extractor_pre_aggregate_commit.json',200000);commit=None
    if b:
        rr=json.loads(b);assert isinstance(rr,list) and len(rr)==1
        commit=rr[0]['sha'];assert re.fullmatch('[0-9a-f]{40}',commit)
        request(f'{RAW}ibllib/{commit}/ibllib/io/extractors/training_trials.py','training_trials.py',250000)
        request(f'{RAW}ibllib/{commit}/ibllib/io/raw_data_loaders.py','raw_data_loaders.py',250000)
    task=f'{RAW}iblrig/{RIG}/tasks/_iblrig_tasks_trainingChoiceWorld/'
    for f in ['_iblrig_tasks_trainingChoiceWorld.py','trial_params.py','task_settings.py']:
        request(task+f,'rig374_'+f,150000)
    request(DOC,'official_trial_data_documentation.html',1800000)
    IO['public_body_read_bytes']+=spent-sum(r['received_bytes'] for r in prior)
    save('OFFICIAL_SOURCE_PINS.json',dict(utc=utc(),historical_extractor_commit=commit,registered_task_release='3.7.4',
        registered_task_release_commit=RIG,cumulative_additional_public_body_bytes=spent,
        evaluation_plus_text_http_bytes=458383178+spent,all_requests=all_requests,
        not_proven='The exact historical extractor build deployed for the aggregate/session is not identified by the registered protocol tag.'))
    receipt('OFFICIAL_SOURCE','complete',public_http_body_bytes=spent,all_jobs_terminal=True)
if __name__=='__main__':
    try:main()
    except BaseException as exc:receipt('OFFICIAL_SOURCE_FAILURE','failed',error=repr(exc));raise
