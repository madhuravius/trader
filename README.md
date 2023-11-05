# Trader

**This is an experiment and is highly unstable.**

**Experiment** I've been starting to play with: [SpaceTraders API](https://docs.spacetraders.io/quickstart/new-game)

API that's being used for consumption: 
[link](https://stoplight.io/api/v1/projects/spacetraders/spacetraders/nodes/reference/SpaceTraders.json?fromExportButton=true&snapshotType=http_service&deref=optimizedBundle)

## Usage

If you already have an API token for an existing agent, ensure it is in `./.token`.

To register a new agent, just use the `register` command. There are enough commands with the CLI wrapping the API
commands to effectively complete the tutorial [here](https://docs.spacetraders.io/quickstart/new-game).

Intended actual use case is for using the CLI for information or kicking off jobs to interact and debug automation-heavy
processes. 

```bash
make install-lock
# OPTIONAL - recommended you run migrations first
make migrations

source ./.venv/bin/activate # or activate.fish
python ./trader/cli.py
```

If you make changes to `trader/dao/*.py`, you should probably run `make migrations` so that there's idempotence for
existing db caches.

Environment variables that might make life easier debugging:

```sh
# SQL_DEBUG will print sql logs, so omit if not desired
# DEBUG will print logs to std out instead of out.log
SQL_DEBUG=1 DEBUG=1 python ./trader/cli.py $COMMAND
```

This can be run with docker as well (note that you'll want to reset the database each time you have an updated image unless
you want to run the migrations locally. all data is just cached local and can be lost each run):

```sh
# copy db.db to local disk
docker cp $(docker create --name tc ghcr.io/madhuravius/trader):/app/db.db ./db.db

# run with local volumes for these persistent files
docker run \
    -v $PWD/db.db:/app/db.db \
    -v $PWD/.token:/app/.token \
    ghcr.io/madhuravius/trader
```

