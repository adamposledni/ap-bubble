# ap-adams-bubble

Personal "second brain" over work (Microsoft) and personal (Google) data, running locally.
Personal project, not a DataBrothers one: DBI standards, brand and skills do not apply.
Requirements and architecture: `other/REQUIREMENTS.md`.

## Code standards
- Clean code: KISS, SRP, DRY, YAGNI; no large methods, functions or files.
- Logging everywhere, down to trace level.
- Naming convention native to each language (Python: snake_case; TS: camelCase, PascalCase components).

## Repo structure
- `apps/<component>/`: one folder per component (api, job, web app, ...); all code lives here, packages included.
- Component naming: `ap-adams-bubble-<name>` (e.g. `apps/ap-adams-bubble-core`); Python import name `ap_adams_bubble_<name>`.
- `tools/<script>.ps1`: scripts for me (run dev server, deploy, ...); may be empty.
- Root holds only `.claude/CLAUDE.md`, `.gitignore`, `apps/`, `tools/`, `other/` (requirements, notes).

## Stack
- Python + uv; the uv workspace root is `apps/`.
- Frontend: React + TypeScript + Vite, pnpm, Mantine.
- Storage: SQLite.

## Runtime data and accounts
- Runtime data lives outside the repo in `%LOCALAPPDATA%\ap-adams-bubble\` (database, inbox attachments, logs).
- Microsoft and Google are connected data sources only, never the app's identity provider.
- OAuth tokens are stored in Windows Credential Manager.

## Development style
- Do not estimate; ask me.
- When asking several questions, number them, or start briefly and discuss them one by one.
- Never run tests without asking first (FE tests are slow and can hang).
- Build in small increments.
- Git: branch `master`, no remote yet; commit regularly, after each working step (conventional commits).

## UI and UX
- One primary color: indigo.
- Clean, minimalistic design.
- Consistent font sizes, paddings and component looks: use Mantine's theme, not Bootstrap.
