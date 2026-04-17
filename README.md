# Airplane Mode

**Airplane Mode** is a small airline ticketing app for the [Frappe](https://frappeframework.com/) Full-Stack Course. It models airlines, airports, aircraft, flights, passengers, and bookable tickets with optional add-ons.

## Features

- **Master data**: **Airline**, **Airport**, **Airplane**
- **Operations**: **Airplane Flight** (includes a website detail view)
- **Passengers**: **Flight Passenger**
- **Sales**: **Airplane Ticket** with line items (**Airplane Ticket Add-on Item**) and configurable **Airplane Ticket Add-on Type** records

## Requirements

- Python 3.10+
- [Frappe](https://github.com/frappe/frappe) v15 (installed via [bench](https://github.com/frappe/bench))

## Installation

Install the app with [bench](https://github.com/frappe/bench):

```bash
cd /path/to/your-bench
bench get-app <repository-url> --branch develop
bench install-app airplane_mode
```

Replace `<repository-url>` with this repository’s clone URL and adjust `--branch` if you use another default branch.

## Development

### Tests

From your bench directory, with a site that has the app installed:

```bash
bench --site <site-name> set-config allow_tests true
bench --site <site-name> run-tests --app airplane_mode
```

### Code quality

This repo uses **pre-commit** (ruff, ESLint, Prettier, pyupgrade). Enable it locally:

```bash
cd apps/airplane_mode
pre-commit install
```

## CI

GitHub Actions workflows in `.github/workflows/`:

| Workflow | Purpose |
| -------- | ------- |
| **CI** | On pushes to `develop` and on pull requests: provision bench, install the app, build assets, run unit tests. |
| **Tests** | On `main` and `develop` (push and PR): full test run in a bench environment. |
| **Linters** | On pull requests: pre-commit; [Frappe Semgrep rules](https://github.com/frappe/semgrep-rules) and Python checks via Semgrep; [pip-audit](https://pypi.org/project/pip-audit/) for dependency vulnerabilities. |

## License

MIT — see [license.txt](license.txt).
