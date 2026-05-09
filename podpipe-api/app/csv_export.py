from __future__ import annotations

import csv
from io import StringIO

from app.models import ScoredLead


CSV_COLUMNS = [
    "name",
    "twitter_handle",
    "twitter_url",
    "bio",
    "followers",
    "match_score",
    "match_reason",
    "outreach_dm",
]


def leads_to_csv(leads: list[ScoredLead]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for lead in leads:
        writer.writerow({column: getattr(lead, column) for column in CSV_COLUMNS})
    return output.getvalue()
