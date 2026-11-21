# ramottamado/skills

A compendium of agent skills for day-to-day development. Each skill loads automatically when a request matches its description.

## Installing

### Claude Code

Install from the [plugin marketplace](https://code.claude.com/docs/en/plugins/install#add-a-marketplace):

```
/plugin marketplace add ramottamado/skills
/plugin install skills@ramottamado
```

### Antigravity

Install with the [Antigravity CLI](https://antigravity.google/docs/plugins/):

```
agy plugin install https://github.com/ramottamado/skills
```

### npx skills

Install with the [`npx skills`](https://skills.sh) CLI:

```
npx skills add https://github.com/ramottamado/skills
```

### Manual copy

Copy any folder under `skills/` into your agent's skills directory. For example, Claude Code reads `~/.claude/skills/`.

## Skills

| Skill | Use it to |
| --- | --- |
| [`skill-authoring`](skills/skill-authoring/SKILL.md) | Create, edit, or review a skill in this repository |
| [`python-dependency-management`](skills/python-dependency-management/SKILL.md) | Add, remove, update, sync, and troubleshoot Python (>=3.12) dependencies, dependency groups, and workspace members with uv |
| [`devcontainer`](skills/devcontainer/SKILL.md) | Create or update a VS Code Dev Containers `devcontainer.json` running on Podman for Python, Java, or mixed Python and Java projects |
| [`static-analysis`](skills/static-analysis/SKILL.md) | Run static analysis with shared complexity thresholds: PMD for Java and Lizard for Python |
| [`cai-apps`](skills/cai-apps/SKILL.md) | Deploy and operate Cloudera AI Applications: create from a manifest, set env vars and secrets, restart, verify, troubleshoot, write launchers |
| [`coding-standards`](skills/coding-standards/SKILL.md) | Apply baseline naming, readability, error-handling, and testing conventions in Python, Java, and TypeScript |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
