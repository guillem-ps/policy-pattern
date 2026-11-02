-- Index supporting View.read_tuples_for_subject(). Without it, a query
-- filtered only by the subject columns has no index to use — the
-- primary key is ordered object-first.
CREATE INDEX IF NOT EXISTS authz_tuples_subject_idx
    ON "authz_tuples" (subject_type, subject_id, subject_relation);
