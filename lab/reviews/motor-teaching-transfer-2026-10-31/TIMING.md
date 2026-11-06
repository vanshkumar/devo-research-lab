# Timing clarification

The literal `00:18 UTC` clock label in the frozen CONTRARY_AMENDMENT.md was manually entered ahead of the actual tool clock. It is incorrect; the later-probe run had already completed at00:17:15 UTC. Preserve the original amendment bytes and its SHA256 rather than repairing a frozen record.

The amendment file was created after the first reconstruction/contrary outputs and before later_probe.py was executed. LATER_PROBE.json records its actual computed UTC creation time and the amendment's SHA256. SOURCE_DEFINITION_PINS.json also records file modification times and verifies their ordering against RUN.json/LATER_PROBE.json. The scientific execution order and prospective choice of h={1,2,3,5} are unchanged. Use those actual tool/output times for chronology, rather than the inaccurate manual header.
