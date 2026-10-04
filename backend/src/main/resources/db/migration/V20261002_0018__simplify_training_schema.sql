-- Align the persisted schema with the final TrainFlow business model.
-- Existing case references and pedagogical methods are preserved before the
-- obsolete support tables are removed.

ALTER TABLE training_cases
    ADD COLUMN reference_year INT NULL AFTER reference,
    ADD COLUMN sequence_number INT NULL AFTER reference_year;

UPDATE training_cases
SET reference_year = CAST(SUBSTRING(reference, 4, 4) AS UNSIGNED),
    sequence_number = CAST(SUBSTRING_INDEX(reference, '-', -1) AS UNSIGNED);

ALTER TABLE training_cases
    MODIFY COLUMN reference_year INT NOT NULL,
    MODIFY COLUMN sequence_number INT NOT NULL,
    ADD CONSTRAINT uq_training_cases_year_sequence UNIQUE (reference_year, sequence_number);

ALTER TABLE training_program_items
    ADD COLUMN method_type JSON NULL AFTER content,
    ADD COLUMN duration_hours DECIMAL(8,2) NOT NULL DEFAULT 0.00 AFTER practice_minutes;

UPDATE training_program_items item
SET item.method_type = COALESCE(
        (SELECT JSON_ARRAYAGG(methods.method)
         FROM training_program_item_methods methods
         WHERE methods.training_program_item_id = item.id),
        JSON_ARRAY()
    ),
    item.duration_hours = ROUND((item.theory_minutes + item.practice_minutes) / 60, 2);

ALTER TABLE training_program_items
    DROP CHECK ck_training_program_items_position_positive;

ALTER TABLE training_program_items
    MODIFY COLUMN method_type JSON NOT NULL,
    RENAME COLUMN position TO order_index;

ALTER TABLE training_program_items
    ADD CONSTRAINT ck_training_program_items_order_index_positive CHECK (order_index > 0);

DROP TABLE training_program_item_methods;
DROP TABLE training_case_counters;
