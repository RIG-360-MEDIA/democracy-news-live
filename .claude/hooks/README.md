# .claude/hooks/

This folder holds Claude Code hook scripts — short executables that run at
defined points in the tool-use lifecycle. They enforce a rule **mechanically**
rather than asking the model to remember.

The folder is intentionally empty. Add a hook only when a rule is being
violated often enough that prose in `CLAUDE.md` isn't holding the line.

---

## When to add a hook

- **PreToolUse / Bash** — block destructive commands by pattern, e.g. reject
  `rm -rf` outside `node_modules` and `.next`.
- **PostToolUse / Edit** — run Prettier or ESLint on changed files, reject the
  edit if it would introduce a lint error.
- **UserPromptSubmit** — auto-attach context. E.g. always include
  `STRUCTURE.md` when the prompt mentions "where".
- **SessionStart** — print the git status and current branch so the assistant
  doesn't have to ask.

## When NOT to add a hook

- To enforce style rules that should live in ESLint/Prettier directly. Hooks
  are a worse place for that.
- To intercept and rewrite the model's output. Fragile, debug nightmare.
- "Just in case." Every hook is one more thing to maintain.

## Hook file shape

A hook is configured in `.claude/settings.json` under `hooks.<eventName>` and
points to a script in this folder. Conventions:

- Single-purpose, < 50 lines.
- Exit 0 to allow, non-zero to block (with a one-line stderr message).
- Fast — under 200ms. A slow hook makes the assistant feel broken.
- Idempotent — running twice does not change the outcome.

## Reference

https://docs.claude.com/en/docs/claude-code/hooks
