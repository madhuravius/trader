# Trader

Experiment to start to play with: [SpaceTraders API](https://docs.spacetraders.io/quickstart/new-game)

API that's being used for consumption: 
[link](https://stoplight.io/api/v1/projects/spacetraders/spacetraders/nodes/reference/SpaceTraders.json?fromExportButton=true&snapshotType=http_service&deref=optimizedBundle)

## Usage

If you already have an API token for an existing agent, ensure it is in `./.token`.

To register a new agent, just use the `register` command. There are enough commands with the CLI wrapping the API
commands to effectively complete the tutorial [here](https://docs.spacetraders.io/quickstart/new-game).

Intended actual use case is for using the CLI for information or kicking off jobs to interact and debug automation-heavy
processes. 

```bash
make install
# OPTIONAL - recommended you run migrations first
make migrations

source ./.venv/bin/activate # or activate.fish
python ./cli.py
```

