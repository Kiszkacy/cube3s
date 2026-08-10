

# IMPORTANT: for module to be able to switch to another module, it would have to request it here
# modules cannot import main.py, so they write a pending switch request here
# main.py polls each loop and executes the actual switch


_pending_module_switch: str | None = None


# TODO: make modules be identifiable by an enum/int instead of a string to improve performance and typos
def request_module_switch(name: str):
    global _pending_module_switch
    _pending_module_switch = name


def consume_pending_module_switch() -> str | None:
    global _pending_module_switch
    pending: str | None = _pending_module_switch
    _pending_module_switch = None
    return pending
