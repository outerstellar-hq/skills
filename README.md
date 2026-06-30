# Skills

Reusable agent skills for code analysis, auditing, database maintenance, and quality automation.

Each directory contains a complete skill with its own `SKILL.md`, supporting documentation, and scripts. Skills can be installed by linking or copying them into your agent's skills directory.

## Available Skills

| Skill | Description |
|-------|-------------|
| **fallback-audit** | Scans codebases for useless fallback patterns (F001–F012) across 7 languages. Catches silent null defaults, empty catch blocks, fallback chains, and other defensive programming that hides real errors. ~95% of fallbacks are unnecessary — this scanner finds the candidates, you decide. |
| **squash-flyway-migrations** | Consolidates accumulated Flyway database migration files into a single baseline. Handles schema dumps, flyway_schema_history cleanup, extension dependencies (pgvector, PostGIS), and platform JAR boundaries. Use when migrations have grown cluttered or when preparing a clean baseline for a major release. |

## Installing a Skill

### OpenCode

```bash
# Clone the repo
git clone https://github.com/outerstellar-hq/skills.git

# Link the skill into your skills directory
New-Item -ItemType Junction -Path "$env:USERPROFILE\.config\opencode\skills\fallback-audit" `
    -Target "path\to\skills\fallback-audit" -Force
```

### ZCode / Claude Code

```bash
# Link into project-level skills
ln -s /path/to/skills/squash-flyway-migrations .agents/skills/squash-flyway-migrations

# Or link into user-level skills (available everywhere)
ln -s /path/to/skills/squash-flyway-migrations ~/.agents/skills/squash-flyway-migrations
```

### Manual copy

```bash
cp -r squash-flyway-migrations/ ~/.agents/skills/
```

## Developing a New Skill

1. Create a directory with your skill name
2. Write `SKILL.md` with YAML frontmatter (`name`, `description`) and markdown body
3. Include scripts, fixtures, and supporting files in `scripts/` or `references/`
4. Follow progressive disclosure: keep `SKILL.md` under 500 lines, push detail to `references/`
5. Add the skill to the table above with a concise description

### Skill format

```yaml
---
name: my-skill
description: What it does and when to trigger it. Be specific about contexts.
---

# My Skill

Body content loaded when the skill triggers.
```

The `description` is the primary trigger signal — include both *what* the skill does and *when* it should fire. Models tend to under-trigger, so list the user phrases that should activate it.
