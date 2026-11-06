# Preserved initial runtime benchmark failure

The first `fit_transition.py --audit --benchmark` attempt on 2026-10-29 passed
all synthetic chronology checks, then stopped before any forecast because the
first original fitting subject, IBL-T1, has only 402 indexed opportunities. The
common reader returned those already-consumed rows and `prefix_future` rejected
the missing 1,000+3,000 horizon. No independent observations were opened.

The runtime benchmark now selects the first fitting subject with at least 4,000
opportunities in the existing footer-derived coverage metadata (NYU-07). This
changes no fitting grid, objective, model, final particle count or exposure cap.
The finite fit separately records every short fitting subject's disposition.
