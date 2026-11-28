#!/usr/bin/env python3
"""A tiny todo list manager that persists tasks to a JSON file."""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

DEFAULT_FILE = Path.home() / ".todo.json"


def load_tasks(path):
    """Load tasks from a JSON file. A missing file means an empty list."""
    path = Path(path)
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError(f"{path} does not contain a list of tasks")
    for index, task in enumerate(data, start=1):
        problem = _task_problem(task)
        if problem:
            raise ValueError(f"task #{index} in {path} {problem}")
    return data


def _task_problem(task):
    """Describe what is wrong with a loaded task, or return None if it is valid."""
    if not isinstance(task, dict):
        return "is not an object"
    if not isinstance(task.get("id"), int) or isinstance(task["id"], bool):
        return "has no integer 'id'"
    if not isinstance(task.get("text"), str):
        return "has no 'text'"
    if not isinstance(task.get("done"), bool):
        return "has no true/false 'done'"
    return None


def save_tasks(path, tasks):
    """Write tasks to a JSON file, creating parent folders if needed.

    The data goes to a temporary file that then replaces the old one, so a crash
    or full disk mid-write never leaves a truncated task list behind.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(tasks, indent=2) + "\n")
        if path.exists():
            os.chmod(tmp_name, path.stat().st_mode & 0o7777)  # keep the old file's permissions
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def add_task(tasks, text):
    """Append a new task and return it.

    The new ID is one more than the highest existing ID, so IDs of other tasks
    never change. Removing the task with the highest ID frees that ID again.
    """
    text = text.strip()
    if not text:
        raise ValueError("Task text cannot be empty")
    next_id = max((task["id"] for task in tasks), default=0) + 1
    task = {"id": next_id, "text": text, "done": False}
    tasks.append(task)
    return task


def find_task(tasks, task_id):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise KeyError(f"No task with id {task_id}")


def complete_task(tasks, task_id):
    """Mark a task as done and return it."""
    task = find_task(tasks, task_id)
    task["done"] = True
    return task


def remove_task(tasks, task_id):
    """Remove a task and return it."""
    task = find_task(tasks, task_id)
    tasks.remove(task)
    return task


def clear_tasks(tasks, done_only=False):
    """Remove all tasks (or only completed ones). Returns how many were removed."""
    before = len(tasks)
    tasks[:] = [task for task in tasks if done_only and not task["done"]]
    return before - len(tasks)


def format_task(task):
    mark = "x" if task["done"] else " "
    return f"{task['id']:>3}. [{mark}] {task['text']}"


def build_parser():
    parser = argparse.ArgumentParser(description="A tiny todo list stored in a JSON file.")
    parser.add_argument(
        "--file",
        default=str(DEFAULT_FILE),
        help=f"path to the JSON file (default: {DEFAULT_FILE})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a new task")
    add.add_argument("text", nargs="+", help="task description")

    lst = sub.add_parser("list", help="show tasks")
    lst.add_argument("--pending", action="store_true", help="only show unfinished tasks")

    done = sub.add_parser("done", help="mark a task as done")
    done.add_argument("id", type=int, help="task id")

    remove = sub.add_parser("remove", help="delete a task")
    remove.add_argument("id", type=int, help="task id")

    clear = sub.add_parser("clear", help="delete all tasks")
    clear.add_argument("--done", action="store_true", help="only delete completed tasks")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        tasks = load_tasks(args.file)
    except (OSError, ValueError) as exc:
        print(f"Error: could not read {args.file}: {exc}", file=sys.stderr)
        return 1

    try:
        if args.command == "add":
            task = add_task(tasks, " ".join(args.text))
            message = f"Added task {task['id']}: {task['text']}"
        elif args.command == "list":
            shown = [t for t in tasks if not (args.pending and t["done"])]
            if not shown:
                print("No tasks.")
            for task in shown:
                print(format_task(task))
            return 0
        elif args.command == "done":
            task = complete_task(tasks, args.id)
            message = f"Completed task {task['id']}: {task['text']}"
        elif args.command == "remove":
            task = remove_task(tasks, args.id)
            message = f"Removed task {task['id']}: {task['text']}"
        elif args.command == "clear":
            count = clear_tasks(tasks, done_only=args.done)
            message = f"Removed {count} task(s)."
    except (KeyError, ValueError) as exc:
        print(f"Error: {exc.args[0]}", file=sys.stderr)
        return 1

    try:
        save_tasks(args.file, tasks)
    except OSError as exc:
        print(f"Error: could not save {args.file}: {exc}", file=sys.stderr)
        return 1
    print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
