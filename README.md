# cube3s

## Development

```sh
./deploy.sh
```

This bumps `BUILD` in `src/version.py`, syncs the version into `pyproject.toml`, copies `src/` onto the device and opens the REPL. Press CTRL+D to restart with the newly uploaded version.

Only the files edited since the last deploy are uploaded, so use `./deploy-all.sh` to push all of `src/` regardless of edit time (after a reflash, or when the device state is unknown). Both scripts skip `*.example.py` and `__pycache__`.

The upload is flat: `src/modules/clock.py` ends up as `/clock.py` next to `/main.py` on the device, so `src/modules/` is only a repository convention and modules are imported as `import clock`. File names have to stay unique across `src/`.

`MAJOR` (new features) and `MINOR` (fixes) must be bumped by hand in `src/version.py`.

## Conventions

- A `__B` suffix on a function name means it is **blocking** (it waits until the operation finishes). Everything else should return immediately.
