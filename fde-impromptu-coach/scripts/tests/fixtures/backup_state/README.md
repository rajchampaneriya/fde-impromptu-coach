# Learner state fixture (sanitised)

Taken from `fde-impromptu-backup` at commit e6987b1 (2026-11-07): 30 legato and 40 pronunciation sessions.
Only the fields the passage-rotation evals read are kept: date, day_number, source, recorded, passage_id,
and for legato flow_level, feedback (the flow tap) and response_prompt. Audio paths, video links, notes,
paragraph text, hard words and streaks were removed. `config.json` keeps only the legato and
pronunciation settings the migration eval checks.
