-- Store version 3 -- ruling R21, row 3e.
--
-- `Provenance` gains `source_version`: the SOURCE's own version, never ours.
-- INTERFACE.md 10b.5 contortion 12 is the finding -- a UC3 type derived from a
-- 2017-10-04 snapshot of a "Historical data" dataset is a different claim from one
-- proposed off a daily feed, and none of the ten Provenance fields had a home for it
-- (`Citation.retrieved_at` is when WE fetched; `imported_from` is foreign system
-- identifiers). EDGES.md gave `EdgeProvenance` the field first, leaving two shapes for
-- one concept with one of them missing it.
--
-- On an APPROVED entry the value lives inside `oo_type.provenance_json`, where every
-- other provenance field lives, so `oo_type` needs no column. A PROPOSAL is written
-- before its Provenance exists, so the value has to survive on the proposal row until
-- approval -- otherwise `propose_type(source_version=...)` accepts a value and loses
-- it, which is worse than not accepting one.
--
-- ADD COLUMN, not drop-and-recreate: this one is additive and nullable, so there is
-- nothing to discard. 9.4's permission is spent only where it buys something (9.6).

ALTER TABLE oo_proposal ADD COLUMN source_version TEXT;
