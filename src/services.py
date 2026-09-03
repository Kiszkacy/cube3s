import auto_brightness
import humidifier


_AVAILABLE_SERVICES: dict[str, object] = {
    "auto_brightness": auto_brightness,
    "humidifier": humidifier,
}


_active_services: set[str] = set()


def available_services() -> tuple[str, ...]:
    return tuple(_AVAILABLE_SERVICES.keys())


def set_active_services(service_names: tuple[str, ...]):
    global _active_services

    target_active: set[str] = set()
    for name in service_names:
        if name in _AVAILABLE_SERVICES:
            target_active.add(name)
        else:
            print(f"[SERVICES] unknown predefined service: '{name}'.")

    for active_name in _active_services - target_active:
        if service_module := _AVAILABLE_SERVICES.get(active_name):
            service_module.deinitialize()

    for name in target_active - _active_services:
        if service_module := _AVAILABLE_SERVICES.get(name):
            service_module.initialize()

    _active_services = target_active


def update():
    for name in _active_services:
        if service_module := _AVAILABLE_SERVICES.get(name):
            service_module.update()
