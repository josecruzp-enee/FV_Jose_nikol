import unittest

from ui.state_helpers import ensure_dict, merge_defaults, sync_fields


class Ctx:
    pass


class TestUIStateHelpers(unittest.TestCase):
    def test_ensure_dict(self):
        ctx = Ctx()
        d = ensure_dict(ctx, "foo", lambda: {"a": 1})
        self.assertEqual({"a": 1}, d)
        self.assertIs(d, ctx.foo)

    def test_merge_defaults(self):
        dst = {"a": 10}
        out = merge_defaults(dst, {"a": 1, "b": 2})
        self.assertEqual({"a": 10, "b": 2}, out)

    def test_sync_fields_dict_and_callable(self):
        d = {"a": 1}
        sync_fields(d, {"a": "x"})
        self.assertEqual(1, d["x"])

        def cb(m):
            m["z"] = 99

        sync_fields(d, cb)
        self.assertEqual(99, d["z"])


if __name__ == "__main__":
    unittest.main()
