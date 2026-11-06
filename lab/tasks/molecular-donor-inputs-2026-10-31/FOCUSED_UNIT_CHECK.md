# Follow-up after the small HDF5 sample

2026-10-31, after the saved MOUSE_SAMPLE_CHECK and offline MOUSE_UNITS_CHECK.
The original nine-range sample ended honestly at 9,119,076 physical bytes;
its attempt to open X metadata failed at its own ceiling. The offline pass
reached donor categories but required an uncached physical span. Preserve both.

The source-linked HDF5 sample is now inspected: expected root/observation/feature
structure, correct official length and a stable ETag. This permits a focused
follow-up acquisition under the original tranche, not another search route.
Use at most FOUR additional public requests, fetching the exact required HDF5
spans rather than another coarse MiB block. Decode only donor/sample/batch/study
metadata, no expression. The overall 40 requests/1 GB ingress/2 GB reads remain.
Stop primary certification if biological unit identities/definitions are not
certified. Do not use batches, cell counts or unknown donor labels as animals.
No later acquisition, representation repair or selected-table substitute follows.
