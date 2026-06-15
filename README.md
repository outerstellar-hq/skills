# Skills

Reusable agent skills for code analysis, auditing, and quality automation.

Each directory contains a complete skill with its own `SKILL.md`, supporting documentation, and scripts. Skills can be installed by linking or copying them into your agent's skills directory.

## Available Skills

| Skill | Description |
|-------|-------------|
| **fallback-audit** | Scans codebases for useless fallback patterns (F001–F012) across 7 languages. Catches silent null defaults, empty catch blocks, fallback chains, and other defensive programming that hides real errors. ~95% of fallbacks are unnecessary — this scanner finds the candidates, you decide. |

## Installing a Skill

### OpenCode

```bash
# Clone the repo
git clone https://github.com/outerstellar-hq/skills.git

# Link the skill into your skills directory
New-Item -ItemType Junction -Path "$env:USERPROFILE\.config\opencode\skills\fallback-audit" `
    -Target "path\to\skills\fallback-audit" -Force
```

### Manual copy

```bash
cp -r fallback-audit/ ~/.config/opencode/skills/
```

## Developing a New Skill

1. Create a directory with your skill name
2. Write `SKILL.md` following the [opencode skill format](https://opencode.ai/docs/skills)
3. Include scripts, fixtures, and any supporting files in `scripts/`
4. Create `scripts/verify-scan.ps1` (or equivalent) to test against fixtures
5. Add a reference entry with your skill's description and coverage matrix
