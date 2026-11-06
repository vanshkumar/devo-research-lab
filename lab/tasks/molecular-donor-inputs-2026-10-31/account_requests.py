"""Summarize this tranche's saved acquisition records, without network access."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
requests = json.loads((root / 'REQUESTS.json').read_text())
out = {'shell_attempts_including_failed_dns': len(requests), 'provider_operations': 5,
       'total_charged_requests': len(requests) + 5,
       'remaining_requests': 40 - len(requests) - 5,
       'measured_application_ingress_bytes': sum(x['bytes_received'] for x in requests),
       'provider_ingress_allowance_bytes': 10_000_000,
       'sample_range_ingress_bytes': sum(x['bytes_received'] for x in requests if '_block_' in x['label']),
       'instrumented_acquisition_peak_rss_bytes': max(x['peak_rss_bytes_macos'] for x in requests)}
(root / 'REQUEST_CHECKPOINT.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
