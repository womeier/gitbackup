Backup git repositories
-----------------------

This script backs up git repositories from `github` or `gitolite` in a folder.
The design goal is simplicity.

If a repo is already present it is updated with the `--ff-only` flag.

## Usage
When properly configured, run `./update.py`.

## Currently supported
- github
- gitolite

## Configuration
The script expects a `config.py` at the root of the repo.

See the example configuration in `./example-config/config.py`
