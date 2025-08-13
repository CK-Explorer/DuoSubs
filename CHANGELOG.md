## v1.0.0 (2025-08-13)

### Feat

- add Web UI launcher for Google Colab
- change `duosubs_gr_blocks` to `create_duosubs_gr_blocks` for clarity
- decrease the default cache delete frequency to 1 hour
- reduce the time of cache delete frequency and age
- **cli**: add `share` option to launch command
- **cli**: added `merge` and `launch-webui` commands
- expose duosubs_gr_blocks in __init__.py
- **duosubs/webui**: add webui

### Fix

- **docs,ui**: correct typos in Google Colab links in README, documentation, and web UI
- patch pynvml.nvmlInit to ensure the gpu_count is initialised correctly
- correct function patches
- **ci**: add playwright installation
- **ci**: pin scipy-stubs for older Python to avoid install errors
- correct the divider of RAM usage
- correct type annotation for gr.Blocks context manager

### Refactor

- move all the constants from layout.py to constants.py
- update import to use duosubs.common.enums
- move strip_ansi to utils.py for reuse

## v0.2.0 (2025-07-23)

### Feat

- include leftover tokens during last neighbour merge

### Fix

- prevent index out of range

## v0.1.0 (2025-07-21)

### Feat

- Initial release
