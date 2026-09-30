# SimpleBooking ChatGPT Plugin

ChatGPT skills for SimpleBooking hotel customers — reservation insights, revenue
analysis, content audit, and demand capture — built on the SimpleBooking IBE and
BackOffice MCP servers.

This is the ChatGPT counterpart of
[simplebooking-claude-plugin](https://github.com/qntweb/simplebooking-claude-plugin):
same four skills, same two MCP servers, same version number for the same skill content.
The package follows the [Agent Plugins](https://developers.openai.com/plugins/build/plugins)
portable format, so it also installs in Codex.

## Prerequisite: the `chatgpt` OAuth client

The SimpleBooking authorization server (`https://auth.simplebooking.it/connect/`)
supports neither dynamic client registration (DCR) nor Client ID Metadata Documents
(CIMD), so ChatGPT connects with the predefined client **`chatgpt`**, as the Claude
plugin uses `claude`.

The Claude plugin declares its client ID in `.mcp.json`. The ChatGPT format has no
field for it (the `mcp.json` schema admits only `type`, `url` and `headers`): the
client ID is entered where each MCP server is registered as an app in ChatGPT
(**Plugins → + → Connection → OAuth**). It is not in any file of this repo.

On the SimpleBooking side, the `chatgpt` client must be a public client (PKCE `S256`,
token auth `none`) with these redirect URIs allowlisted:

| Surface | Redirect URI |
|---|---|
| ChatGPT web, desktop, mobile | `https://chatgpt.com/connector_platform_oauth_redirect` — the server publishes `authorization_response_iss_parameter_supported: true`, so ChatGPT uses the stable URI. The exact one is shown on the app's page in ChatGPT |
| Codex CLI | `http://127.0.0.1/callback` (loopback) |

## Install

### Option A — ZIP upload (quickest for testing)

Requires a ChatGPT Business or Enterprise workspace, and either the **Upload plugins
with custom MCP servers** permission or the workspace owner/admin role.

1. **Settings → Security and login → Developer mode** on.
2. In [ChatGPT Plugins](https://chatgpt.com/plugins), create one app per MCP server
   (`https://mcp.backoffice.simplebooking.it`, `https://mcp.ibe.simplebooking.it`),
   OAuth with client ID `chatgpt`. Copy each app ID from the browser URL
   (`plugin_asdk_app_…`).
3. Build the archive:

   ```bash
   python3 scripts/build-zip.py \
       --backoffice-app plugin_asdk_app_... --ibe-app plugin_asdk_app_...
   ```

   Output: `dist/simplebooking-<version>-web.zip`, which references those two apps
   through `.app.json`. The app IDs belong to that workspace, so the archive does too.
4. **Admin → Plugins → Upload plugin**, select the ZIP, then set who can install it.

Without the two IDs, `build-zip.py` produces the `-desktop.zip` variant, which ships
`mcp.json`. ChatGPT marks any plugin that declares servers in `mcp.json` **Desktop
only**: it runs only in the ChatGPT desktop app, never on web or mobile.

### Option B — GitHub catalog (like the Claude plugin)

The catalog is `.agents/plugins/marketplace.json`. A workspace admin imports it once and
ChatGPT keeps it in sync:

1. **Admin → Plugins → Add → Import marketplace**.
2. **Source**: `https://github.com/qntweb/simplebooking-chatgpt-plugin`; leave **Path**
   empty; optionally a branch or tag.
3. Authorize GitHub access (private repositories are supported), review the import
   results, then set the installation policy per role.

ChatGPT checks the repository daily; **Admin → Plugins → Marketplaces → Sync now**
forces an update. This is the counterpart of **Sync** in Claude.

As committed here, the plugin ships `mcp.json`, so it imports as **Desktop only**.
For web use the imported plugin needs a `.app.json` pointing at apps registered *in
that workspace* — a per-workspace file, which is why it isn't committed.

Codex CLI reads the same catalog:

```bash
codex plugin marketplace add qntweb/simplebooking-chatgpt-plugin
```

### Option C — Public Plugins Directory

The only channel that reaches every ChatGPT user without per-workspace setup. See the
requirements below.

## Public Plugins Directory: requirements

| Area | Requirement |
|---|---|
| Publisher | Organization on the [OpenAI Platform](https://platform.openai.com) with **business verification** under the name shown in the listing; submitters need **Apps Management → Write** |
| Submission | Portal at [platform.openai.com/plugins](https://platform.openai.com/plugins), type **With MCP**: the MCP server is submitted directly by URL, `mcp.json` and `.app.json` are not used, skills are uploaded as a bundle or imported with **Scan Tools** |
| MCP servers | Public production HTTPS URL. The form takes **one** MCP server URL; this plugin has two (see open questions) |
| Domain verification | The token issued by the portal served as plain text at `https://<mcp host or parent>/.well-known/openai-apps-challenge` |
| Tools | Every tool with accurate `readOnlyHint`, `openWorldHint`, `destructiveHint` and a written justification for each; clear names and descriptions; minimal inputs; no internal IDs, trace IDs or debug fields in responses |
| Authentication | OAuth 2.1 per the MCP authorization spec. For workspace domain restrictions: a UserInfo endpoint returning `email` and `email_verified: true`, with `openid` and `email` scopes enabled |
| Reviewer account | Working login and password for a demo account with sample data, no MFA, SMS or email confirmation |
| Listing | Name, short and long description, category, square logo (PNG/JPEG/WebP/SVG, 48–4096 px, ≤ 5 MiB), website, **support**, **privacy policy** and **terms** URLs, all public HTTPS and matching the publisher |
| Privacy policy | Categories of personal data, purposes, recipients, retention, user controls |
| Tests | At least 5 positive and 3 negative test cases, reproducible without internal context |
| Other | Starter prompts, countries of availability, release notes |

After approval, the publisher decides when to publish. Tool changes are then picked up
by continuous review; changes to the listing or the skills need a new version and
another review.

## Update

- ZIP upload: build a new archive with a new `version` and upload it again.
- GitHub catalog: merge to the tracked branch; ChatGPT syncs daily.
- Codex CLI: `codex plugin marketplace upgrade`.

## What's included

- **sb-reservation-insights** — pick-up, on the books, pace YoY, channel mix,
  commissions, cancellations, booking window, arrivals, markets, services,
  payments.
- **sb-revenue-lens** — demand-driven revenue diagnostic: money leaks, unsold
  risk, MinLOS restrictions, direct-vs-OTA parity.
- **sb-hotel-content-audit** — content and translation completeness audit
  across the SimpleBooking platform.
- **sb-demand-capture** — cross-checks area demand against actual reservations
  to tell whether a property is capturing the demand of its own destination.

## Layout

```text
.agents/plugins/marketplace.json   GitHub catalog (one plugin)
scripts/build-zip.py               ZIP for Upload plugin, desktop or web variant
simplebooking/
├── plugin.json                    portable manifest + extensions.com.openai
├── mcp.json                       the two SimpleBooking MCP servers
├── assets/                        composer icon and logo (square, placeholders)
└── skills/<skill>/
    ├── SKILL.md
    └── agents/openai.yaml         ChatGPT presentation and MCP dependencies
```

`simplebooking/skills/` is generated from the skills repository with
`scripts/build-client-plugin.py --target chatgpt --plugin-dir <this repo>/simplebooking`, never edited
here. `agents/openai.yaml` lives with each skill's source, so the build carries it.

## License

[PolyForm Shield 1.0.0](LICENSE) — © 2025-2026 QNT S.r.l. — Zucchetti Group.
