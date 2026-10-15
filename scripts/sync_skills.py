#!/usr/bin/env python3
"""Generate small provider entry points from the shared skill catalogue."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def expected(base, installed=False, provider="both", source=ROOT):
    catalog = json.loads((Path(source) / "skills/catalog.json").read_text(encoding="utf-8"))
    prefix = "../../../.nox-lite/" if installed else "../../../"
    values = {}
    for platform in ([".agents", ".claude"] if provider == "both" else [".agents" if provider == "codex" else ".claude"]):
        for skill in catalog:
            folder = Path(base) / platform / "skills" / skill["name"]
            body = f'---\nname: {skill["name"]}\ndescription: {json.dumps(skill["description"])}\n---\n\n'
            body += f'# {skill["title"]}\n\nRead and follow [the shared procedure]({prefix}workflows/{skill["workflow"]}.md). '
            body += 'Resolve personal paths from the workspace root containing `workspace.json`. '
            body += 'If no workspace exists, guide setup first. Read the shared operating rules in `AGENTS.md`. '
            body += 'Apply existing human authorization within its scope; skill selection itself grants no external-action authority.\n'
            values[folder / "SKILL.md"] = body
            if platform == ".agents":
                values[folder / "agents/openai.yaml"] = (
                    f'interface:\n  display_name: {json.dumps(skill["title"])}\n'
                    f'  short_description: {json.dumps(skill["short"])}\n'
                    f'  default_prompt: {json.dumps("Use $" + skill["name"] + " to " + skill["prompt"])}\n'
                    'policy:\n  allow_implicit_invocation: true\n')
    return values


def generate(base=ROOT, installed=False, provider="both", check=False, source=ROOT):
    changed = []
    for path, text in expected(base, installed, provider, source).items():
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            changed.append(str(path))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    return changed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = generate(check=args.check)
    print(f'{len(changed)} skill files {"need updating" if args.check else "updated"}.')
    if args.check and changed:
        raise SystemExit(1)
