---
name: vtex-app-source-download
description: Baixa o código-fonte de uma versão publicada de um app VTEX IO direto do Registry da VTEX (infra.io.vtex.com), usando o token da sessão do VTEX CLI. Use sempre que precisar ver o código que está de fato instalado numa loja VTEX — quando o repositório não bate com a versão do `vtex ls`, quando não há repositório nenhum, para descobrir o que mudou entre versões, para auditar credenciais/rotas de um app em produção, ou para recuperar um app antes de corrigir e republicar. Dispare também em pedidos como "baixa o app da master", "qual o código da versão X.Y.Z", "o repo está desatualizado em relação à loja", "compara o app publicado com o repo" ou "quero ver o fonte do app do vendor Z", mesmo que o usuário não fale em registry.
---

# Baixar código-fonte de apps VTEX IO pelo Registry

Todo `vtex publish` envia os arquivos do app para o Registry da VTEX, e o
Registry guarda esses arquivos por versão. Então, mesmo sem acesso ao repositório
original, dá para recuperar exatamente o código que foi publicado em qualquer
versão — o que resolve o caso clássico de "o repo diz 1.0.0, a loja roda 1.1.1 e
ninguém sabe o que tem nela".

As rotas são as mesmas que o client `Registry` do `@vtex/api` usa (o próprio VTEX
CLI tem o arquivo em `node_modules/@vtex/api/lib/clients/infra/Registry.js`).

## Pré-requisitos

- VTEX CLI instalado e **logado na conta**: `vtex login <account>`. O token fica em
  `~/.vtex/session/tokens.json`, uma entrada por conta. Ele expira; se vier 401/403,
  peça para o usuário logar de novo (o login abre o navegador, então sugira que ele
  rode `! vtex login <account>` no próprio prompt).
- Saber o app (`vendor.nome`) e a versão. Se o usuário não souber a versão
  instalada, rode `vtex ls` logado na conta — ele lista "Installed Apps" no
  workspace master com a versão de cada um.

## Fluxo

Use o script empacotado, que só faz GET e nunca imprime o token:

```bash
SCRIPT=~/.claude/skills/vtex-app-source-download/scripts/vtex_registry.py

# 1. versões publicadas (não traz data de publicação)
python3 $SCRIPT versions <account> <vendor.app>

# 2. arquivos de uma versão
python3 $SCRIPT files <account> <vendor.app> <versao>

# 3. baixar o fonte
python3 $SCRIPT download <account> <vendor.app> <versao> <pasta_destino>
#   --include-dist  para trazer também o build (dist/) — raramente necessário
```

Escolha uma pasta de destino com a versão no nome (`<app>-<versao>/`) e fora de
qualquer repositório git, para não comitar por acidente (veja "Segredos" abaixo).

### Como o download é organizado

| No registry | Na pasta baixada | O que é |
|---|---|---|
| `src/...` | raiz (`node/`, `react/`, `manifest.json`, `CHANGELOG.md`...) | O que o desenvolvedor publicou — é isto que se compara com o repo |
| `manifest.json`, `service.json`, `routes.json`, `bundle.ts`, `public/` | `_registry/` | Gerado pelo builder no publish |
| `dist/...`, `dependencies.tar.zst` | ignorado (a menos que `--include-dist`) | Saída compilada e dependências |

Apps com builder `node` têm o fonte em `src/node/`; apps React em `src/react/`;
os demais builders seguem o mesmo padrão (`src/<builder>/`).

## Comparar com um repositório

O diff ingênuo costuma acusar quase todos os arquivos, porque quem publicou do
Windows deixa CRLF. Compare ignorando fim de linha e espaços:

```bash
diff -r -q --strip-trailing-cr -w -B \
  -x _registry -x node_modules -x '.*' -x __tests__ \
  <repo>/<pasta-do-app> <pasta_baixada>
```

e depois `diff --strip-trailing-cr -w` nos arquivos que sobrarem.

Duas diferenças são esperadas e não indicam mudança de código:
- `node/tsconfig.json` (ou equivalente): o builder reescreve com caminhos
  `/cache/build/...`.
- Lockfiles (`yarn.lock`, `package-lock.json`) podem existir só de um lado.

Se só o `version` do `manifest.json` diferir, o repo **é** o código em produção;
basta subir o número da versão no repo antes do próximo publish (por exemplo,
publicada 1.1.1 → próxima 1.1.2). Isso evita criar um app novo só para
"contornar" o descompasso.

## Apps de outros vendors

O registry da conta também responde por apps de outros vendors instalados ou
públicos (testado: `vtex.my-account` listado e com arquivos a partir da conta
de uma loja). Então não é preciso logar na conta do vendor para ler. Ainda
assim, lembre o usuário de que código de terceiros tem licença própria — ler para
entender ou depurar é uma coisa, copiar para outro projeto é outra.

## Segredos e segurança

- O fonte publicado vem como foi escrito: se alguém colocou appKey/appToken,
  tokens de API ou senhas no código, eles estarão na pasta baixada. Ao reportar o
  que encontrou, **mascare** valores sensíveis (mostre só o nome da chave ou os
  primeiros caracteres) e avise o usuário para não comitar nem compartilhar a
  pasta.
- Achar uma credencial no código é um achado de segurança por si só: o registry
  guarda todas as versões, então a credencial continua acessível ali mesmo
  depois de removida do repo. A recomendação é rotacionar.
- O Registry também tem rotas de escrita (publish, `PATCH` de
  deprecate/undeprecate/validate). Esta skill não usa nenhuma delas; se o usuário
  pedir algo assim, use os comandos oficiais do CLI (`vtex deprecate`,
  `vtex publish`) e confirme antes.
- O token da sessão é do usuário logado e dá acesso à conta. Nunca o imprima,
  nunca o coloque em arquivos e não o envie para outro host que não
  `infra.io.vtex.com`.

## Rotas (para chamadas manuais)

Base: `https://infra.io.vtex.com/apps/v0/{account}/master/registry`,
header `Authorization: bearer <token>`. O workspace é sempre `master`.

| Ação | Rota | Resposta |
|---|---|---|
| Listar versões | `GET /{vendor.app}` | `{"data":[{"versionIdentifier":"vendor.app@1.2.3","location":...}]}` |
| Listar arquivos | `GET /{vendor.app}/{versao}/files` | `{"data":[{"path":"src/node/index.ts"}, ...]}` |
| Baixar arquivo | `GET /{vendor.app}/{versao}/files/{path}` | conteúdo bruto |

O registry não informa data de publicação nem quem publicou. Para saber quando
uma versão entrou, a única pista local é o `CHANGELOG.md` do próprio app (que
costuma estar desatualizado).
