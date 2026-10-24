---
description: Propose a change to a shared contract following PRD §B.0
argument-hint: <contract id, e.g. B6> <short description>
---

The developer wants to change contract $ARGUMENTS. Follow PRD §B.0 exactly. Do not edit any file until step 4.

1. Read PRD Part B for that contract, its schema in `contracts/`, its examples, and the contract table in `contracts/CLAUDE.md` (owner and users).
2. Classify the change:
   - **Additive and optional** (new optional field; readers that ignore it still work): allowed after Release 0.
   - **Breaking** (rename, remove, type change, new required field, changed meaning): needs a new version (`v2`) and the guide's approval. Say so clearly and stop unless the developer confirms the guide approved.
3. Write a short proposal: what changes, why, which requirement IDs need it, every module and test affected (search the code for uses), and a migration note for breaking changes.
4. After the developer says go, prepare **one** branch that changes together: the schema, the examples, the PRD Part B text, and the tests of every affected module. Run `/preflight`.
5. Draft the pull request description listing every affected owner as a required reviewer plus the guide.
