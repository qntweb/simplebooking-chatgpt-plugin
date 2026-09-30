#!/usr/bin/env python3
"""
Package simplebooking/ as a ZIP archive for ChatGPT's "Upload plugin"
(Admin > Plugins) or for the submission portal.

Two variants, because ChatGPT treats them differently:

  desktop (default)  ships mcp.json. ChatGPT marks any plugin that declares MCP
                     servers in mcp.json "Desktop only": it installs and runs
                     only in the ChatGPT desktop app.

  web                --backoffice-app and --ibe-app given. Ships .app.json,
                     which references the two MCP servers already registered
                     as apps in the target ChatGPT workspace, and drops
                     mcp.json. Works on web, desktop and mobile. The app IDs
                     belong to that workspace, so the archive does too.

App IDs are accepted as shown in the browser URL (plugin_asdk_app_...) or bare
(asdk_app_...): the plugin_ prefix is stripped, as .app.json wants the app ID.

Usage:
    python3 scripts/build-zip.py
    python3 scripts/build-zip.py --backoffice-app plugin_asdk_app_... --ibe-app plugin_asdk_app_...

Output: dist/simplebooking-<version>-<variant>.zip, one top-level simplebooking/
directory and nothing beside it (the upload validator rejects siblings).
"""
import argparse
import json
import os
import re
import sys
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_DIR = os.path.join(REPO_ROOT, "simplebooking")
DIST_DIR = os.path.join(REPO_ROOT, "dist")
APP_ID = re.compile(r"^(asdk_app_|connector_|templated_apps_)[A-Za-z0-9][A-Za-z0-9_-]*$")
SKIP_NAMES = {".DS_Store", "__pycache__"}


def app_id(value, flag):
    bare = value[len("plugin_"):] if value.startswith("plugin_") else value
    if not APP_ID.match(bare):
        sys.exit(f"ERROR: {flag} {value!r} is not an app ID "
                 "(expected asdk_app_..., connector_... or templated_apps_...).")
    return bare


def plugin_files():
    for root, dirs, files in os.walk(PLUGIN_DIR):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_NAMES)
        for name in sorted(files):
            if name in SKIP_NAMES or name.endswith(".pyc"):
                continue
            path = os.path.join(root, name)
            yield path, os.path.relpath(path, PLUGIN_DIR)


def main():
    parser = argparse.ArgumentParser(description="Package the plugin as a ZIP for ChatGPT.")
    parser.add_argument("--backoffice-app", metavar="ID",
                        help="App ID of the BackOffice MCP server registered in the workspace")
    parser.add_argument("--ibe-app", metavar="ID",
                        help="App ID of the IBE MCP server registered in the workspace")
    args = parser.parse_args()

    if bool(args.backoffice_app) != bool(args.ibe_app):
        sys.exit("ERROR: pass both --backoffice-app and --ibe-app for the web variant, or neither.")
    web = bool(args.backoffice_app)

    with open(os.path.join(PLUGIN_DIR, "plugin.json")) as f:
        manifest = json.load(f)
    version = manifest["version"]
    variant = "web" if web else "desktop"
    extra = {}

    if web:
        manifest["extensions"]["com.openai"]["apps"] = "./.app.json"
        extra["plugin.json"] = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        extra[".app.json"] = json.dumps({"apps": {
            "simplebooking-backoffice": {"id": app_id(args.backoffice_app, "--backoffice-app"),
                                         "required": True},
            "simplebooking-ibe": {"id": app_id(args.ibe_app, "--ibe-app"), "required": True},
        }}, indent=2) + "\n"

    os.makedirs(DIST_DIR, exist_ok=True)
    out = os.path.join(DIST_DIR, f"simplebooking-{version}-{variant}.zip")
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, rel in plugin_files():
            if rel in extra or (web and rel == "mcp.json"):
                continue
            zf.write(path, os.path.join("simplebooking", rel))
            count += 1
        for rel, content in extra.items():
            zf.writestr(os.path.join("simplebooking", rel), content)
            count += 1

    print(f"Done: {count} files, variant {variant}, written to {os.path.relpath(out, REPO_ROOT)}")
    if not web:
        print("NOTE: this variant is Desktop only in ChatGPT. For the web, register the two MCP "
              "servers as apps and pass their IDs with --backoffice-app and --ibe-app.")


if __name__ == "__main__":
    main()
