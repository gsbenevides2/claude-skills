# claude-skills

Minhas skills do Claude Code. Cada pasta na raiz é uma skill (`<nome>/SKILL.md`).

| Skill | O que faz |
|---|---|
| [vtex-app-source-download](vtex-app-source-download/SKILL.md) | Baixa o código-fonte de versões publicadas de apps VTEX IO pelo Registry da VTEX, usando a sessão do VTEX CLI |

## Instalação

O Claude Code procura skills em `~/.claude/skills/<nome>/SKILL.md`, então clone o repo
em qualquer lugar e crie um link para cada skill:

```bash
git clone git@github.com:gsbenevides2/claude-skills.git ~/personal/claude-skills
cd ~/personal/claude-skills
for d in */; do [ -f "$d/SKILL.md" ] && ln -sfn "$PWD/${d%/}" ~/.claude/skills/"${d%/}"; done
```

Com o link, um `git pull` já atualiza as skills.

## Adicionar uma skill

1. Crie a pasta `<nome>/` com o `SKILL.md` (frontmatter com `name` e `description`).
2. Rode o loop de instalação acima para criar o link.
3. Acrescente uma linha na tabela deste README.
