# Source-faithfulness and contribution gate — CLOSE

Fixed question: does the reported recovery carry from the follow-up's approximate corruption to the original bilinear procedure in the same ResNet18/CIFAR10 case? This allocation selected only the original Achille–Rovere–Soatto study and the direct Pawlak follow-up. It did not reopen generic exposure matching or restart discovery.

| Requirement | Observed evidence | Gate status |
| --- | --- | --- |
| Original deficit/recovery | Original arXiv1711.08856v3 §2: bilinear32→8→32;160later clean epochs. AppendixA.1 specifies ResNet18, initial rate.1, factor.97/epoch and weight decay.0005. | Published description verified; original implementation/checkpoints and baseline unverified. |
| Follow-up deficit/recovery | Pawlak arXiv2510.09687v1 §2.1–2.2.2: ResNet18/CIFAR10; batch128; matching listed rate/decay/weight decay; extrapolated CIFAR-C pixelate9;160clean epochs; restart to initial rate substantially reduces the gap. | Description verified; severity9 extrapolation formula/code/weights unverified. Restart is already prior work. |
| Closest material contrary | Follow-up §2.2.3 already reports corruption-type/severity dependence. It does not certify this exact bilinear-versus-pixelate recovery comparison. | Exact transport is unresolved, but mismatch alone earns no consequential result. Operational learning equivalence and finite-training variation are live alternatives. |
| Release lead | Targeted original/follow-up queries and GitHub title/owner queries yielded no verified exact release. The original-paper Code link on the simplicity-bias index actually opens Accordion; its README names a different study and cites Achille as inspiration. | Reject that link as original code. Finite search only; no global nonexistence assertion. |
| Executable feasibility | Local environment inventory succeeds; no torch/torchvision in the inspected project environment. | No measured learning throughput. No verified exact checkpoint or original-model/task execution. |
| Material/cost gate | No original baseline, exact follow-up corruption object, observed recovery contrast or measured total training cost. | NOT EARNED; CLOSE before training. |

Sources: [original](https://arxiv.org/html/1711.08856v3), [follow-up](https://arxiv.org/html/2510.09687v1), [follow-up metadata](https://arxiv.org/abs/2510.09687), [mislabelled index](https://sadimanna.github.io/simplicity-bias-papers/), [actual link target](https://github.com/uw-mad-dash/Accordion). See exact operation/results in [receipts](SOURCE_BROWSE_RECEIPTS.json).

Original interpolation library/coordinate/antialias details and ResNet implementation choices were not certified here. The follow-up restart description does not certify optimizer-momentum/BN-state handling. This limits a claim of exact reproduction; it is not an accusation of a source defect. A source-independent reimplementation would require explicit choices and a new justified baseline validation, rather than silently claiming byte-faithful execution.

The strongest pro-investment reading remains possible: a carefully implemented original bilinear case might show that the known restart rescue transports. But this run has only the protocol mismatch, not evidence of an important exception or affordable discriminating experiment. Main training, a third-family search and a manufactured numerical or independent-review milestone are not justified by this gate.
