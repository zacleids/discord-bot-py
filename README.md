# discord-bot-py

A Discord bot with a small Flask backend and a shared set of utility modules.

## Running the app

To run the Discord bot or web backend, create a `.env` file with `DISCORD_TOKEN` set. You can copy `.env.example` to `.env` and add a bot token that has access to one of your Discord servers.

The bot also supports `HOME_TIMEZONE` for features that depend on "today", including the daily fortune. If unset, it defaults to `US/Pacific`.

Once `DISCORD_TOKEN` is configured, you can start either service or both:

- Discord bot only:
```sh
python run.py --bot
```
- Flask web backend only:
```sh
python run.py --web
```
- Discord bot and web backend together:
```sh
python run.py --bot --web
```

## Development setup

### Create a virtual environment

Using a project-local `.venv` keeps dependencies isolated from the rest of your system.

```sh
python -m venv .venv
```

Activate it with the shell you use:

- Bash, Git Bash, or WSL on Windows:
```sh
source .venv/Scripts/activate
```
- Bash on macOS or Linux:
```sh
source .venv/bin/activate
```
- PowerShell on Windows:
```powershell
.\.venv\Scripts\Activate.ps1
```
- Command Prompt on Windows:
```cmd
.\.venv\Scripts\activate.bat
```

Install dependencies:

```sh
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Deactivate the environment when needed:

```sh
deactivate
```

### Pre-commit hooks

This project uses [pre-commit](https://pre-commit.com/) for import sorting, formatting, and linting.

Install the hooks:

```sh
pre-commit install
```

Run all hooks manually:

```sh
pre-commit run --all-files
```

The configured hook order is:

1. `isort`
2. `black`
3. `flake8`

## Database migrations

Database migration commands and examples are documented in [DB.md](./DB.md).

## Testing

Run the test suite from the project root:

```sh
ENV=TEST pytest
```

## Linting and Code Style

To run the checks manually in the same order as pre-commit:

```sh
isort --check-only .
black --check .
flake8 .
```

- `isort --check-only` verifies import ordering. Auto-fix with `isort .`. ([isort](https://github.com/PyCQA/isort))
- `black --check` verifies formatting. Auto-fix with `black .`. ([black](https://github.com/psf/black))
- `flake8` checks for linting issues.([flake8](https://github.com/pycqa/flake8))


### Links used:
- https://fallendeity.github.io/discord.py-masterclass/slash-commands/#slash-command-parameters
- https://www.tweag.io/blog/2023-04-04-python-monorepo-1/