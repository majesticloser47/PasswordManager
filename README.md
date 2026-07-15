# Sesame — CLI Password Manager

Sesame is a single-user, local-first command-line password manager written in
Python. It derives its keys with Argon2id and encrypts every secret at rest
with AES-256-GCM, storing the encrypted vault in a local SQLite database.

**Status:** Sesame is under active development. Interfaces and internals may
change between releases.

---

## Features

- **Master-password unlock** — a single master password (never stored)
  unlocks the vault for the current session.
- **Two-tier key hierarchy** — Argon2id derives a Key-Encryption-Key (KEK)
  from the master password; the KEK wraps a random 256-bit vault key that
  encrypts your entries.
- **AES-256-GCM everywhere** — the vault key and every stored password entry
  are protected with authenticated encryption (confidentiality + integrity).
- **Pluggable password entropy** — passwords can be generated from a
  cryptographically secure PRNG (CSPRNG, via Python's `secrets` module) or
  from the [ANU Quantum Random Numbers](https://qrng.anu.edu.au/) API, with
  automatic fallback to the CSPRNG if the API is unreachable.
- **Clipboard integration** — generated/fetched passwords are copied to the
  clipboard and automatically cleared after 20 seconds.
- **Local SQLite storage** — a single-file vault database, portable and easy
  to back up.
- **Interactive shell** — a `cmd`-based REPL (`unlock`, `add`, `list`,
  `fetch`, `delete`, `lock`, `exit`) built with
  [Rich](https://github.com/Textualize/rich) for readable output.

---

## How It Works

```
User (terminal)
   │ master password
   ▼
Argon2id KDF ──► KEK (in-memory only, never persisted)
   │
   ▼
AES-256-GCM decrypt ──► vault_key (in-memory only)
   │
   ▼
AES-256-GCM encrypt/decrypt ──► each password entry
   │
   ▼
SQLite database (on disk, ciphertext only)
```

1. On first unlock, Sesame generates a random 256-bit **vault key** (using
   the configured entropy source), wraps it with a KEK derived from your
   master password via **Argon2id**, and stores the wrapped key plus the KDF
   salt/parameters in the `vault` table.
2. On every subsequent unlock, Sesame re-derives the KEK from the master
   password and the stored salt/parameters, then decrypts the vault key. The
   vault key lives only in process memory for the session's duration.
3. Each password entry (service, username, password, notes) is serialized to
   JSON and encrypted with AES-256-GCM using a fresh random nonce, then
   stored in the `entries` table.
4. Locking the vault (`lock`, or exiting the shell) discards the in-memory
   vault key.

---

## Requirements

- Python **3.10+**
- A local, writable filesystem path for the vault database
- OS clipboard support (used by the clipboard-copy feature, via `pyperclip`)
- Network access if using the QRNG entropy source (calls the ANU Quantum
  Random Numbers API); not required for CSPRNG

### Runtime dependencies

| Package                    | Purpose                                              |
| -------------------------- | ---------------------------------------------------- |
| `argon2-cffi`              | Argon2id key derivation                              |
| `cryptography`             | AES-256-GCM authenticated encryption                 |
| `rich`                     | Terminal UI (tables, colored output, panels)         |
| `pyperclip`                | Clipboard read/write/clear                           |
| `Requests`                 | Fetches random bytes from the ANU QRNG API           |
| `typer`                    | CLI argument parsing (`--mode`, `config` subcommand) |
| `simple-toml-configurator` | Reads/writes the app's TOML settings file            |

---

## Installation

You may install Sesame directly using pip:

```bash
pip install git+https://github.com/majesticloser47/PasswordManager
```
Then, simply run the sesame command to start:

```bash
sesame
```

OR clone the repo and set up the virtal environment and dependencies yourself:

```bash
git clone https://github.com/majesticloser47/PasswordManager.git
cd PasswordManager

python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

OR install as an editable package (registers the `sesame` console script):

```bash
pip install -e .
```

The project also has a [uv](https://docs.astral.sh/uv/) lockfile
(`uv.lock`). If you use `uv`, `uv sync` installs the exact locked runtime and
development dependencies in one step.

---

## Configuration

Sesame stores its settings in a TOML config file (managed by
`simple-toml-configurator`) rather than environment variables. By default,
the file lives at `src/sesame/config/config.toml` and is created
automatically.

| Setting              | Default                           | Description                                   |
| -------------------- | --------------------------------- | --------------------------------------------- |
| `vault.db_path`      | `<package dir>/sesame.db`         | Filesystem path to the SQLite vault database. |
| `app.setup_complete` | `false` until first run completes | Internal flag; not user-editable directly.    |

**First run:** the first time you launch Sesame, a setup wizard asks whether
you want to keep the default vault database path or choose a different one.

**Changing settings later:** run the `config` subcommand at any time to view
or update configurable values (currently `db_path`):

```bash
sesame config
```

Avoid pointing `db_path` at a cloud-synced or world-readable location unless
you understand the implications of syncing an encrypted vault file.

---

## Usage

Launch the interactive shell:

```bash
python -m sesame
# or, if installed via pip/setuptools entry point:
sesame
```

By default, the password generator uses the CSPRNG entropy source. To use the
ANU Quantum Random Numbers API instead, pass `--mode`:

```bash
sesame --mode QRNG
```

The active mode is shown in the banner when the shell starts.

To view or change app settings (e.g. the vault database path) instead of
launching the shell, use the `config` subcommand:

```bash
sesame config
```

### Commands

Once inside the interactive shell, the following commands are available:

| Command            | Description                                                                                                                           |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| `unlock`           | Prompts for your master password (hidden input) and unlocks the vault. Sets up a new vault on first run.                              |
| `add`              | Interactively add a new entry (service, username, notes, and either a generated or manually entered password).                        |
| `list`             | Show a table of all saved entries (passwords are masked).                                                                             |
| `fetch <service>`  | Decrypt and copy the password for `<service>` to the clipboard. Prompts for a choice if multiple entries share the same service name. |
| `delete <service>` | Delete the entry for `<service>` after a confirmation prompt.                                                                         |
| `lock`             | Discards the in-memory vault key, re-locking the session.                                                                             |
| `exit`             | Exit the shell.                                                                                                                       |

Most commands require the vault to be unlocked first (`unlock`); otherwise
Sesame prints a "vault is locked" warning.

Copied passwords are automatically cleared from the clipboard after 20
seconds, or immediately on `Ctrl+C`.

---

## Project Structure

```
├── src/sesame/
│   ├── __main__.py                  # module entry point (`python -m sesame`), delegates to cli.py
│   ├── cli.py                       # Typer app: `--mode` option, first-run wizard, `config` subcommand
│   ├── sesame.py                    # SesameShell — the interactive cmd.Cmd REPL
│   ├── config.py                    # Config — TOML-backed settings (vault.db_path, app.setup_complete)
│   ├── config/                      # auto-generated; holds config.toml (gitignored)
│   ├── repository/
│   │   └── db.py                    # SQLite schema + CRUD for vault/entries
│   ├── service/
│   │   ├── encrypt_decrypt.py       # generic AES-256-GCM helpers
│   │   ├── generate_password.py     # PasswordGenerator (uses a pluggable entropy source)
│   │   ├── password_actions.py      # add/list/fetch/delete entry logic
│   │   ├── entropy_sources/
│   │   │   ├── entropy_source.py    # EntropySource abstract base class
│   │   │   ├── csprng.py            # CSPRNG entropy source (secrets.randbelow)
│   │   │   ├── qrng.py              # QRNG entropy source (ANU API, falls back to CSPRNG)
│   │   │   └── entropy_factory.py   # builds an entropy source from EntropySourceEnum
│   │   └── enum/
│   │       └── entropy_sources_enum.py  # EntropySourceEnum: CSPRNG | QRNG
│   ├── util/
│   │   └── functions.py             # clipboard copy/clear helpers
│   └── vault/
│       └── vault.py                 # VaultSession — KDF, key wrap/unwrap, lock/unlock
├── pyproject.toml                   # package metadata, dependencies, tooling config
├── requirements.txt                 # runtime dependencies (pinned)
└── uv.lock                          # locked dependency versions (used by `uv`)
```

---

## Development

Dev/test dependencies (`pytest`, `ruff`, `bandit`, `pre-commit`, `build`,
`python-semantic-release`) are declared as a `dependency-group` in
`pyproject.toml`. Install them with:

```bash
uv sync --group dev
pre-commit install
```

- **Tests:** `pytest`
- **Lint/format:** `ruff check .`
- **Security scan:** `bandit -r src`
- **Pre-commit hooks:** trailing whitespace/EOF fixers, `ruff`, `flake8`,
  `pyupgrade`, and `gitleaks` (secret scanning) also run via
  `.pre-commit-config.yaml`
- **Versioning/release:** managed via `python-semantic-release` (conventional
  commits, configured in `pyproject.toml`)

---

## License

No license file is currently included in this repository. All rights
reserved by the author unless a license is added.
