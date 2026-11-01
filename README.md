# ramottamado/skills

A compendium of agent skills for day-to-day development. Each skill loads automatically when a request matches its description.

## Installing

### Claude Code

Install from the [plugin marketplace](https://code.claude.com/docs/en/plugins/install#add-a-marketplace):

```
/plugin marketplace add ramottamado/skills
/plugin install skills@ramottamado
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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
