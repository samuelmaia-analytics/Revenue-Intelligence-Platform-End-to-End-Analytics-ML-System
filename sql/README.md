# SQL Surface

## Purpose

This directory holds the reference SQL surface for the repository. It should stay aligned with the SQLite-first runtime documented in the root README and downstream smoke checks.

## Directories

## `ddl/`

Reference dimensional DDL split by table. These files should be the most readable form of the schema.

## `analytics/`

Review-friendly analytical queries showing how governed warehouse outputs are consumed downstream.

This folder now also includes a Power BI-oriented scorecard query so BI consumers can reuse governed warehouse semantics instead of rebuilding metrics ad hoc.

## `create_tables.sql`

Bootstrap script for fast local schema creation. Keep it aligned with the `ddl/` files so the consolidated path does not drift from the table-specific definitions.

## Conventions

- prefer SQLite-portable syntax unless a dialect-specific requirement is called out in the file
- use explicit aliases and reviewer-readable metric names
- document non-obvious assumptions close to the query
- keep examples tied to actual warehouse entities produced by the batch pipeline
