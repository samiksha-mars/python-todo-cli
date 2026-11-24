import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from todo import (
    add_task,
    clear_tasks,
    complete_task,
    load_tasks,
    main,
    remove_task,
    save_tasks,
)


class TaskOperationsTest(unittest.TestCase):

    def test_add_assigns_increasing_ids(self):
        tasks = []
        self.assertEqual(add_task(tasks, "first")["id"], 1)
        self.assertEqual(add_task(tasks, "second")["id"], 2)

    def test_ids_not_reused_after_remove(self):
        tasks = []
        add_task(tasks, "a")
        add_task(tasks, "b")
        remove_task(tasks, 1)
        self.assertEqual(add_task(tasks, "c")["id"], 3)

    def test_add_rejects_empty_text(self):
        with self.assertRaises(ValueError):
            add_task([], "   ")

    def test_complete(self):
        tasks = []
        add_task(tasks, "a")
        complete_task(tasks, 1)
        self.assertTrue(tasks[0]["done"])

    def test_unknown_id(self):
        with self.assertRaises(KeyError):
            complete_task([], 42)
        with self.assertRaises(KeyError):
            remove_task([], 42)

    def test_clear_all(self):
        tasks = []
        add_task(tasks, "a")
        add_task(tasks, "b")
        self.assertEqual(clear_tasks(tasks), 2)
        self.assertEqual(tasks, [])

    def test_clear_done_only(self):
        tasks = []
        add_task(tasks, "a")
        add_task(tasks, "b")
        complete_task(tasks, 1)
        self.assertEqual(clear_tasks(tasks, done_only=True), 1)
        self.assertEqual([t["text"] for t in tasks], ["b"])


class StorageTest(unittest.TestCase):

    def test_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load_tasks(Path(tmp) / "nope.json"), [])

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sub" / "todo.json"
            tasks = [{"id": 1, "text": "a", "done": False}]
            save_tasks(path, tasks)
            self.assertEqual(load_tasks(path), tasks)


class MainTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "todo.json")

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["--file", self.path, *args])
        return code, out.getvalue(), err.getvalue()

    def stored(self):
        return json.loads(Path(self.path).read_text())

    def test_add_and_list(self):
        self.run_main("add", "Buy", "milk")
        code, out, _ = self.run_main("list")
        self.assertEqual(code, 0)
        self.assertIn("[ ] Buy milk", out)
        self.assertEqual(self.stored()[0]["text"], "Buy milk")

    def test_done_persists(self):
        self.run_main("add", "task")
        self.run_main("done", "1")
        self.assertTrue(self.stored()[0]["done"])
        _, out, _ = self.run_main("list", "--pending")
        self.assertIn("No tasks.", out)

    def test_remove(self):
        self.run_main("add", "a")
        self.run_main("add", "b")
        self.run_main("remove", "1")
        self.assertEqual([t["text"] for t in self.stored()], ["b"])

    def test_clear(self):
        self.run_main("add", "a")
        self.run_main("add", "b")
        self.run_main("done", "2")
        self.run_main("clear", "--done")
        self.assertEqual([t["text"] for t in self.stored()], ["a"])
        self.run_main("clear")
        self.assertEqual(self.stored(), [])

    def test_unknown_id_returns_error(self):
        code, _, err = self.run_main("done", "7")
        self.assertEqual(code, 1)
        self.assertIn("No task with id 7", err)

    def test_list_empty(self):
        code, out, _ = self.run_main("list")
        self.assertEqual(code, 0)
        self.assertIn("No tasks.", out)


if __name__ == "__main__":
    unittest.main()
