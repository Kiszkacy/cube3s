# cube3s

## Development

```sh
./deploy.sh
```

This bmps `BUILD` in `src/version.py`, syncs the version into `pyproject.toml`, copies `src/` onto the device and opens the REPL. Press CTRL+D to restart with the newly uploaded version.

`MAJOR` (new features) and `MINOR` (fixes) must be bumped by hand in `src/version.py`.

## Conventions

- A `__B` suffix on a function name means it is **blocking** (it waits until the operation finishes). Everything else should return immediately.
