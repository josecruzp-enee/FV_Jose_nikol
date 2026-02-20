import unittest

from ui.state_helpers import (
    build_inputs_fingerprint,
    ensure_dict,
    is_result_stale,
    merge_defaults,
    save_result_fingerprint,
    sync_fields,
)


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

    def test_result_fingerprint_detecta_stale(self):
        ctx = Ctx()
        ctx.datos_cliente = {"cliente": "A"}
        ctx.consumo = {"kwh_12m": [100] * 12}
        ctx.sistema_fv = {"cobertura_objetivo": 0.8}
        ctx.equipos = {"panel_id": "p1", "inversor_id": "i1"}
        ctx.electrico = {"dist_ac_m": 20}

        fp = save_result_fingerprint(ctx)
        self.assertEqual(fp, build_inputs_fingerprint(ctx))
        self.assertFalse(is_result_stale(ctx))

        ctx.consumo["kwh_12m"][0] = 150
        self.assertTrue(is_result_stale(ctx))


if __name__ == "__main__":
    unittest.main()
