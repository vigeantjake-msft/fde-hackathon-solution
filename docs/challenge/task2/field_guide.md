# Task 2 — Field Guide

This is a document-to-record task. Shape the output for machines, not humans.

**Focus on:** `drug_name`, `indications`, `dosage_forms`, `contraindications`, `adverse_reactions`. These carry the scoring weight.

**Watch out for:** section headers that don't match expectations, flattened tables, PDF artifacts, and fields that look present but are actually boilerplate.

**Good solutions tend to:** separate parsing from schema filling, validate before returning, route text and PDF through a shared normalization path, and fail gracefully per-field instead of blowing up the whole extraction.