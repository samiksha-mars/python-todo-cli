#!/usr/bin/env python3
"""A tiny todo list manager that persists tasks to a JSON file."""

import json
from pathlib import Path


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
    return data


def save_tasks(path, tasks):
    """Write tasks to a JSON file, creating parent folders if needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")


def add_task(tasks, text):
    """Append a new task and return it. IDs keep increasing, never reused."""
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
