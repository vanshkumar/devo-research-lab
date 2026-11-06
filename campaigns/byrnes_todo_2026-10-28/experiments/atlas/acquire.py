import pathlib,json,hashlib,urllib.request
BASE=pathlib.Path(__file__).resolve().parents[2];D=BASE/'data/atlas';S=BASE/'sources/atlas'
COMMIT='29599fcb13a74a908c986ad69d68fc3e4a3cf6d0'
FILES=[('paper_figures/revision_figures/suppl_tables/cluster_annotations_and_statistics.txt',294081,'0e90e741e1d98c00b4aad5671ad6f0bd5a3b1596'),('merge_human_mouse_neurons/matched_clusters_scviCorPruned.tsv',118660,'ce4edd9ff8a7121d8026fea89fc40dfb2b9f78f9'),('paper_figures/revision_figures/suppl_tables/human_mouse_corresponding_clusters.txt',46966,'606ffd4f2a8011f87944700e026b3220e927531b'),('paper_figures/revision_figures/suppl_tables/marker_genes_all.txt',16580582,'e749f8a239648fd089c9604b371a8df80f256d96'),('paper_figures/revision_figures/suppl_tables/sup_sample_statistics.txt',11783,'068c5a251abf8daf9db6fa13d9d664b839232c10'),('merge_human_mouse_neurons/05_match_clusters.R',15331,'3d70d2660d571c5fc411066741c6b7ea8026766a'),('merge_human_mouse_neurons/cluster_matching_functions.R',15324,'48aa6b134196db5b5ea3c91ec5ef88042dca89f6'),('paper_figures/supplementary_tables.R',18700,'d019c5efc445698adf2a6f3f6df85b971d83d711')]
FILES += [('integration_pipeline/run_scripts/12_markers_mrtree.R',8747,'12aa18ca1debb405a46f8465c7b00c642f207fef'),('integration_pipeline/stratified_wilcoxon_functions.R',22726,'64db9728fdf362af197f455315c6a3ba6e01eff9'),('integration_pipeline/parameters/parameters_human_hypo_v2.json',2379,'e689e58a5f563ad2391fde37c0939b4a52a60f30')]
manifest=[]
for remote,size,blob in FILES:
 dest=(S if remote.endswith('.R') else D)/pathlib.Path(remote).name;dest.parent.mkdir(parents=True,exist_ok=True)
 url=f'https://raw.githubusercontent.com/lsteuernagel/HYPOMAP/{COMMIT}/{remote}'
 if not dest.exists():
  with urllib.request.urlopen(url,timeout=60) as r:b=r.read(size+1)
  assert len(b)==size,(dest,len(b),size);dest.write_bytes(b)
 b=dest.read_bytes();assert len(b)==size
 assert hashlib.sha1(b'blob '+str(size).encode()+b'\0'+b).hexdigest()==blob
 manifest.append(dict(file=str(dest.relative_to(BASE)),url=url,bytes=size,git_blob=blob,sha256=hashlib.sha256(b).hexdigest()))
 print(dest.name,size,flush=True)
(D/'manifest.json').write_text(json.dumps(dict(commit=COMMIT,files=manifest),indent=2)+'\n')
