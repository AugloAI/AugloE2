# Separate current state, chronology, and sensitive evidence

E2 information is divided by purpose: `project/` owns mutable current-state contracts, Git history records source evolution, `history/events/` holds the append-only Product Chronicle, and Controlled Storage outside Git holds sensitive evidence.

This separation prevents current contracts from becoming event logs, prevents product decisions from being inferred only from commits, and keeps sensitive material out of source control. Chronicle events may reference controlled evidence only by stable ID or hash; corrections and supersessions are appended rather than rewriting accepted events.
