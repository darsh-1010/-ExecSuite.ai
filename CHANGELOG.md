# Changelog

All notable changes to this project will be documented in this file.

## [2026-06-05]
### Added
- Generalized dashboard into **ExecSuite.ai** supporting C-Suite, Marketing, Sales, and Tech Development departments.
- Added dynamic department selection dropdown `#department-select` and dynamic roster container `#agent-roster-list` to HTML frontend.
- Added dynamic agent boardroom rendering with role-specific color-coded avatars.
- Added dynamic border-left styling on message bubbles based on active agent theme.
- Extended test coverage in `backend/tests/test_core.py` with tests for `marketing_campaign` department and runtime setup switches.
- Added `pytest.ini` and `.pylintrc` specifications.

### Changed
- Refactored `backend/core/agent.py` to support 16 dynamic agent personas.
- Refactored `backend/core/organization.py` to route workflow sequences based on selected departments.
- Refactored `backend/app.py` endpoints `/api/state`, `/api/config`, and `/api/run` to support the active department parameter.
- Wrapped long docstrings and prompts to strictly adhere to the 120-character pylint line limit.
- Replaced custom print statements in server execution with clean logger instances.

### Fixed
- Fixed unused typing imports.
- Fixed trailing newline warning.
- Reached exactly 10.00/10.00 score on Pylint across all python modules.
