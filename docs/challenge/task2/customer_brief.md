# Task 2 — Customer Brief

The customer has drug-label content that's only useful once it's structured data. Manual extraction is slow, inconsistent, and doesn't scale.

They want an API: send text or PDF, get back stable JSON. The fields that matter most are adverse reactions, indications, dosage forms, and contraindications.

## What Breaks Trust

- Missing or malformed nested arrays
- Hallucinated fields the document doesn't support
- Inconsistent normalization across similar labels
- Text works fine but PDFs fall apart