# Local source-cache serialization correction

The first source_audit.py invocation exited 1 before calculations or output JSON. The local apply_patch serialization added one terminal newline to each provider-returned source file: first model cache 7,053 bytes/Git SHA1 34fe12b517359b80730985cbc5952ca5e04ed12f instead of the certified 7,052 bytes/c3f313303379eb0725c2c64580ee736a577374b0. This was OUR cache representation, not an author-source discrepancy.

All four initial cache files are preserved under failed_source_cache/; exactly the extra terminal blank line is removed from source/ before a repeat pin/call-graph audit. No model, policy, seed, outcome or stopping rule was changed; no student examples/updates occurred. This bookkeeping correction is not a substantive pre-evaluation revision. Failed-pass process startup/time/RSS/physical I/O were not measured; charge conservatively 1 second and 1 MB separate reads. No new public operation or redownload.
