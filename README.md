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
- A `__RS` suffix on a getter means it **resamples** (it talks to the hardware right away and refreshes the cached value). The plain getter returns the value sampled by that module's `update()`, which is what drawing code should use. Example: `power.battery_level()` is free, `power.battery_level__RS()` costs an I2C transaction.
- MQTT handlers must only **store state** and set a flag, never draw. They run inside `mqtt.check_if_any_message()`, so they can paint over a module that is about to be switched away, or draw to a target the current module never claimed. All drawing belongs in `update()`.
- Helpers with an `update()` (`localtime`, `touch`, `power`) are sampled once per iteration in `main.py`. Modules read the sampled values instead of polling the hardware or `time` on their own.
- A module that calls `display.use_canvas()` in `initialize()` must call `display.use_display()` in `deinitialize()`, and delete every canvas it created with `display.create_canvas()`.
