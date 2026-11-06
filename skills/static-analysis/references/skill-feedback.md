# Skill feedback

Anyone can read a GitHub issue once it is posted. Never include sensitive information, and never post an issue until the user has seen the exact title and body and approved it.

Use this when the user reports that the `static-analysis` skill gave incorrect or outdated guidance, is missing information, or could be improved. This file covers feedback on the skill's instructions, not on the tools the skill describes.

## What not to include

The issue is drafted from the conversation. Remove the following before drafting, and describe the problem in general terms instead:

- Credentials, API tokens, secrets, and passwords
- Account IDs and other resource identifiers
- Customer or personal data, such as names, email addresses, and IP addresses
- Internal hostnames and URLs
- Private code, configuration, and logs

## Steps

1. **Ask permission.** Ask the user whether they want to send feedback to the skill maintainers. If they decline, move on.
2. **Draft the issue.** Write the issue body from the conversation. Name the specific file and section that caused the problem, and describe what you expected compared with what happened. Leave out everything listed in [What not to include](#what-not-to-include).
3. **Review with the user.** Show the user the exact title and body, then ask a yes/no question, such as "Post this as a public issue on ramottamado/skills?" Submit only after the user answers yes. If they ask for changes, apply them and ask again. Agreeing to send feedback in step 1 does not approve the text.
4. **Submit.** Create the issue, for example with `gh issue create --repo ramottamado/skills`. Format the title as `skill-feedback: static-analysis: <summary of the problem>`.
5. **Share the result.** Give the user the issue URL. If submission fails, give the user the approved title and body, along with this link for creating the issue manually: <https://github.com/ramottamado/skills/issues/new>
