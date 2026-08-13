#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
skill = root / "SKILL.md"

errors = []
if not skill.exists():
    errors.append("Falta SKILL.md")
else:
    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append("SKILL.md debe comenzar con frontmatter YAML")
    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append("Frontmatter YAML incompleto")
    else:
        fm = parts[1]
        m_name = re.search(r"^name:\s*([^\n]+)$", fm, re.M)
        m_desc = re.search(r"^description:\s*([^\n]+)$", fm, re.M)
        if not m_name:
            errors.append("Falta name")
        else:
            name = m_name.group(1).strip().strip('"\'')
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
                errors.append(f"name inválido: {name}")
            if len(name) > 64:
                errors.append("name supera 64 caracteres")
            if name != root.name:
                errors.append(f"El directorio '{root.name}' no coincide con name '{name}'")
        if not m_desc:
            errors.append("Falta description")
        elif len(m_desc.group(1).strip()) > 1024:
            errors.append("description supera 1024 caracteres")

refs = [
    "decision-engine.md",
    "stack-routing.md",
    "research-policy.md",
    "figma-workflow.md",
    "implementation-safety.md",
    "visual-qa.md",
    "ux-audit-checklist.md",
    "output-contracts.md",
    "source-baseline.md",
]
for ref in refs:
    if not (root / "references" / ref).exists():
        errors.append(f"Falta references/{ref}")

if errors:
    print("Skill inválida:")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("OK: estructura y metadatos básicos válidos")
