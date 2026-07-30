# IMPORTANT: deploy.sh parses and rewrites BUILD here, keep the "NAME: int = number" shape intact

MAJOR: int = 0 # bumped by hand on new features
MINOR: int = 1 # bumped by hand on fixes
BUILD: int = 0 # bumped by deploy.sh on every deploy, never resets


VERSION: str = f"{MAJOR}.{MINOR}.{BUILD}"
