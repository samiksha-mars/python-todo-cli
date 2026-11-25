# Python Todo CLI

A small command-line todo list that stores tasks in a JSON file.
Uses only the Python standard library.

## Features

- `add`, `list`, `done`, `remove`, and `clear` subcommands
- Tasks persisted to a human-readable JSON file (default `~/.todo.json`)
- `--file` option to keep separate lists (e.g. per project)
- `list --pending` hides completed tasks; `clear --done` removes only completed tasks
- Task IDs stay stable: removing a task never renumbers the others

## Usage

```bash
python3 todo.py add Buy milk
# Added task 1: Buy milk

python3 todo.py add Write report
python3 todo.py done 1
python3 todo.py list
#   1. [x] Buy milk
#   2. [ ] Write report

python3 todo.py list --pending   # only unfinished tasks
python3 todo.py remove 2         # delete a task
python3 todo.py clear --done     # delete completed tasks
python3 todo.py clear            # delete everything

# Use a different file (the --file option goes before the subcommand)
python3 todo.py --file work.json add Review PR
```

## Tests

```bash
python3 -m unittest
```
