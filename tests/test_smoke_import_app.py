import importlib
import unittest


class TestSmokeImportApp(unittest.TestCase):
    def test_import_app_and_critical_modules(self):
        app_mod = importlib.import_module("app")
        yaml_loader_mod = importlib.import_module("electrical.catalogos_yaml")
        orq_mod = importlib.import_module("core.orquestador")

        self.assertIsNotNone(app_mod)
        self.assertIsNotNone(yaml_loader_mod)
        self.assertIsNotNone(orq_mod)


if __name__ == "__main__":
    unittest.main()
