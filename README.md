# Club Discord Bot

A Discord bot for club operations, with:

- Member contribution submissions (via a private modal)
- HR workflows to review/approve/reject contributions
- Staff moderation commands (mute/unmute/warn/warnings/clear) with optional log channel
- Club “organizational roles” and departments stored in SQLite (independent of Discord roles)

## Requirements

- Python 3.11+ recommended
- A Discord application + bot token

## Setup

1. Create a virtual environment (recommended) and install dependencies:

```bash
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
```

2. Create your environment file:

- Copy `.env.example` to `.env`
- Fill in `DISCORD_TOKEN` at minimum

3. Run the bot:

```bash
python run.py
```

## Configuration

All configuration is done via environment variables (loaded from `.env`).

- `DISCORD_TOKEN` (**required**): your bot token
- `HR_ROLE_NAME` (default `HR`): Discord role name that grants HR commands
- `STAFF_ROLE_NAME` (default `Staff`): Discord role name that grants staff commands (HR is treated as staff too)
- `GUILD_ID` (optional): when set, slash commands sync to that guild only (faster for development)
- `LOG_CHANNEL_ID` (optional): a channel ID where moderation actions are logged
- `DATABASE_PATH` (default `club_bot.db`): path to the SQLite database file
- `COMMAND_RESPONSES_PUBLIC` (default `true`): if true, command replies are public; if false, replies are private (ephemeral)

## Commands

### Member commands

- `/contribute`: submit a contribution to HR via a private modal
- `/contributions my [limit]`: view your own submissions

### HR commands

- `/contributions list [member] [limit]`
- `/contributions latest [limit]`
- `/contributions pending [limit]`
- `/contributions approve <contribution_id>`
- `/contributions reject <contribution_id>`

- `/role create <name> [description]`
- `/role delete <name>`
- `/role assign <user> <role>`
- `/role remove <user> <role>`
- `/role list`
- `/role members <role>`
- `/role user <user>`

- `/role department create <name> [description]`
- `/role department assign <department> <role_ids>`
- `/role department remove <department> <role_ids>`
- `/role department list`
- `/role department delete <name>`

### Staff commands

- `/mute <member> <duration_minutes> [reason]`
- `/unmute <member> [reason]`
- `/warn <member> <reason>`
- `/warnings <member>`
- `/clear <amount>`
- `/modlogs [member] [limit]`

### Owner/admin commands

- `/admin ping`
- `/admin stats`
- `/admin db-path`

## Development

Install dev tooling:

```bash
python -m pip install -r requirements-dev.txt
```

Run formatting/lint/typecheck/tests:

```bash
ruff format .
ruff check .
mypy src
pytest -q
```

## Notes

- This project uses **discord.py 2.x** and **slash commands** (app commands).
- The SQLite database schema is created on startup (`init_db()`).

