# Agent Execution Prompt for Pricewatch Improvements

> **Copy and paste this prompt to start or continue improvement work**

---

## 🚀 START NEW SESSION PROMPT

```
You are working on improving the Pricewatch application. Your ONLY source of truth is the file `IMPROVEMENT_PLAN.md` in this repository.

## CRITICAL RULES - YOU MUST FOLLOW THESE

1. **READ FIRST**: Before doing ANY work, read `IMPROVEMENT_PLAN.md` completely to understand the current state
2. **CHECK PROGRESS**: Look at the "Status Updates" section at the bottom of `IMPROVEMENT_PLAN.md` to see:
   - Current Phase
   - Current Task
   - Any blockers
3. **SEQUENTIAL EXECUTION**: Complete tasks in EXACT order - do NOT skip ahead
4. **MARK COMPLETION**: After completing each subtask (e.g., 1.1.1), update the checkbox in `IMPROVEMENT_PLAN.md` from `[ ]` to `[x]`
5. **UPDATE STATUS**: After each task group (e.g., 1.1, 1.2), update the "Status Updates" section with:
   - Current Phase
   - Current Task  
   - Last Updated date
   - Any blockers encountered
6. **ATOMIC COMMITS**: After completing each major task (e.g., 1.1, 1.2), the work should be committable
7. **TEST AFTER PHASE**: Run `pytest tests/ -v` after completing each phase before moving to next
8. **NO DEVIATION**: Do NOT add features, improvements, or changes not specified in the plan
9. **ACCEPTANCE CRITERIA**: A task is only complete when ALL acceptance criteria are met

## YOUR WORKFLOW

1. Read `IMPROVEMENT_PLAN.md`
2. Find the first unchecked `[ ]` task
3. Execute that specific task
4. Mark it complete `[x]`
5. Update status section
6. Repeat until phase complete
7. Run tests
8. Move to next phase

## START NOW

Read `IMPROVEMENT_PLAN.md` and begin work on the next incomplete task. Report:
- Which phase you're on
- Which task you're starting
- What files you'll modify

Then execute the task.
```

---

## 🔄 CONTINUE SESSION PROMPT

```
Continue working on Pricewatch improvements following `IMPROVEMENT_PLAN.md`.

1. Read `IMPROVEMENT_PLAN.md` to find current progress
2. Identify the next unchecked task `[ ]`
3. Execute that task completely
4. Mark checkbox as complete `[x]`
5. Update the "Status Updates" section at the bottom
6. Report what you completed and what's next

Do NOT skip tasks. Do NOT reorder. Follow the plan exactly.
```

---

## ✅ VERIFY PROGRESS PROMPT

```
Read `IMPROVEMENT_PLAN.md` and provide a progress report:

1. How many tasks are complete vs total in each phase?
2. What is the current task being worked on?
3. Are there any blockers documented?
4. What percentage of the overall plan is complete?

Present this as a table and summary.
```

---

## 🧪 PHASE COMPLETION PROMPT

```
I've completed Phase [X] of the improvement plan.

1. Run the full test suite: `pytest tests/ -v`
2. Verify all acceptance criteria for Phase [X] are met
3. Update `IMPROVEMENT_PLAN.md` progress tracker table to show Phase [X] as "✅ Complete"
4. Document any issues found
5. Confirm ready to proceed to Phase [X+1]
```

---

## 🛑 BLOCKER PROMPT

```
I've encountered a blocker on task [X.X.X] in `IMPROVEMENT_PLAN.md`.

1. Document the blocker in the "Status Updates" section of `IMPROVEMENT_PLAN.md`
2. Explain what the blocker is
3. Suggest possible solutions
4. Continue to the next task that is NOT blocked
5. Return to blocked task when resolved

Update the plan file with blocker details.
```

---

## 📊 STATUS CHECK PROMPT

```
Before we continue, read `IMPROVEMENT_PLAN.md` and tell me:

1. Current Phase: ?
2. Current Task: ?
3. Last completed task: ?
4. Next task to do: ?
5. Any blockers: ?
6. Estimated tasks remaining in current phase: ?

Then ask if I want you to continue with the next task.
```

---

## 🎯 SINGLE TASK PROMPT

```
Execute ONLY task [X.X] from `IMPROVEMENT_PLAN.md`.

1. Read the task requirements from the plan
2. Execute all subtasks (X.X.1, X.X.2, etc.) in order
3. Mark each subtask complete as you finish
4. Verify acceptance criteria are met
5. Update status section
6. STOP after this task - do not continue to next task

Report what was done and confirm completion.
```

---

# Quick Reference

| Action | Prompt to Use |
|--------|---------------|
| Start fresh | START NEW SESSION PROMPT |
| Continue work | CONTINUE SESSION PROMPT |
| Check progress | VERIFY PROGRESS PROMPT |
| Finish a phase | PHASE COMPLETION PROMPT |
| Report a blocker | BLOCKER PROMPT |
| Quick status | STATUS CHECK PROMPT |
| Do one task only | SINGLE TASK PROMPT |

---

# Example Usage

**You say:**
```
Continue working on Pricewatch improvements following `IMPROVEMENT_PLAN.md`.

1. Read `IMPROVEMENT_PLAN.md` to find current progress
2. Identify the next unchecked task `[ ]`
3. Execute that task completely
4. Mark checkbox as complete `[x]`
5. Update the "Status Updates" section at the bottom
6. Report what you completed and what's next

Do NOT skip tasks. Do NOT reorder. Follow the plan exactly.
```

**Agent will:**
1. Read the improvement plan
2. Find task 1.1.1 (first unchecked)
3. Execute it
4. Update the markdown file
5. Report completion
6. Ask to continue or stop

---

*Use these prompts to maintain strict adherence to the improvement plan across multiple sessions.*

