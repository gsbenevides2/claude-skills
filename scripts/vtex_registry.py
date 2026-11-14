#!/usr/bin/env python3
"""Baixa o código-fonte de uma versão publicada de um app VTEX IO pelo Registry.

Usa o token da sessão do VTEX CLI (~/.vtex/session/tokens.json), então é
preciso ter rodado `vtex login <account>` antes. Só faz GET: não publica,
não deprecia, não altera nada no registry. O token nunca é impresso.

Uso:
  vtex_registry.py versions <account> <vendor.app>
  vtex_registry.py files    <account> <vendor.app> <versao>
  vtex_registry.py download <account> <vendor.app> <versao> <pasta_destino> [--include-dist]
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://infra.io.vtex.com/apps/v0/{account}/master/registry"


def load_token(account):
    path = os.path.expanduser("~/.vtex/session/tokens.json")
    try:
        with open(path) as f:
            tokens = json.load(f)
    except FileNotFoundError:
        sys.exit(f"Não achei {path}. Rode `vtex login {account}` primeiro.")
    token = tokens.get(account)
    if not token:
        sys.exit(f"Sem token para a conta '{account}'. Rode `vtex login {account}`.")
    return token


def get(account, token, rel_path):
    url = BASE.format(account=account) + "/" + urllib.parse.quote(rel_path, safe="/@.")
    req = urllib.request.Request(url, headers={"Authorization": f"bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            sys.exit(
                f"HTTP {e.code} em {rel_path}: token expirado ou sem acesso. "
                f"Rode `vtex login {account}` e tente de novo."
            )
        if e.code == 404:
            sys.exit(f"HTTP 404 em {rel_path}: app ou versão não existe nesse registry.")
        raise


def list_versions(account, token, app):
    data = json.loads(get(account, token, app))["data"]
    return [v["versionIdentifier"].split("@", 1)[1] for v in data]


def list_files(account, token, app, version):
    data = json.loads(get(account, token, f"{app}/{version}/files"))["data"]
    return [f["path"] for f in data]


def download(account, token, app, version, out_dir, include_dist):
    out_dir = os.path.abspath(out_dir)
    paths = list_files(account, token, app, version)
    saved, skipped = 0, 0
    for p in paths:
        if not include_dist and (p.startswith("dist/") or p.endswith(".tar.zst")):
            skipped += 1
            continue
        # src/ é o que o desenvolvedor publicou -> vai para a raiz da pasta.
        # O resto (manifest.json, service.json, routes.json, bundle.ts...) é
        # gerado pelo builder -> vai para _registry/ para não confundir.
        rel = p[len("src/"):] if p.startswith("src/") else os.path.join("_registry", p)
        dest = os.path.normpath(os.path.join(out_dir, rel))
        if not dest.startswith(out_dir + os.sep):
            print(f"ignorado (caminho fora da pasta): {p}", file=sys.stderr)
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(get(account, token, f"{app}/{version}/files/{p}"))
        saved += 1
    print(f"{saved} arquivos salvos em {out_dir} ({skipped} de dist/ ignorados)")


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    cmd, account, app = argv[0], argv[1], argv[2]
    token = load_token(account)
    if cmd == "versions":
        print("\n".join(list_versions(account, token, app)))
    elif cmd == "files" and len(argv) >= 4:
        print("\n".join(list_files(account, token, app, argv[3])))
    elif cmd == "download" and len(argv) >= 5:
        download(account, token, app, argv[3], argv[4], "--include-dist" in argv)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
