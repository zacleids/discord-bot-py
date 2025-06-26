# discord-bot-py

## Running discord-bot and/or web backend

In order to run the discord bot or web backend, you need a .env file with the `DISCORD_TOKEN` filled out. You can copy the `.env.example` file to `.env` and add your bot token that has access to a discord server of your choice.

Once the `DISCORD_TOKEN` has been added, you can run the bot, web backend, or both:

- To run the Discord bot only:
  ```sh
  python run.py --bot
  ```
- To run the Flask web backend only:
  ```sh
  python run.py --web
  ```
- To run both the Discord bot and web backend together:
  ```sh
  python run.py --bot --web
  ```

## Development Setup

This project uses [pre-commit](https://pre-commit.com/) hooks for formatting and linting.
To set up:

```sh
pip install pre-commit
pre-commit install
```

This will automatically run checks before you commit.
You can run all hooks manually with:

```sh
pre-commit run --all-files
```

## Testing

To run the test suite:

```sh
ENV=TEST pytest
```

## Linting & Code Style

To check code style and linting manually, run:

```sh
flake8 .
black --check .
isort --check-only .
```

- `flake8` checks for general linting issues. ([flake8](https://github.com/pycqa/flake8))
- `black --check` checks code formatting (auto-format with `black .`). ([black](https://github.com/psf/black))
- `isort --check-only` checks import order (auto-fix with `isort .`). ([isort](https://github.com/PyCQA/isort))


### Links used:
- https://fallendeity.github.io/discord.py-masterclass/slash-commands/#slash-command-parameters
- https://www.tweag.io/blog/2023-04-04-python-monorepo-1/