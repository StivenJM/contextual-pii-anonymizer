import unittest

from contextual_pii_anonymizer.evaluation import evaluate_scenarios
from contextual_pii_anonymizer import process_text
from contextual_pii_anonymizer.detection import is_valid_ec_cedula, is_valid_ec_ruc


class PipelineTests(unittest.TestCase):
    def test_validates_ec_cedula(self):
        self.assertTrue(is_valid_ec_cedula("1711122232"))
        self.assertFalse(is_valid_ec_cedula("1711122233"))

    def test_validates_ruc_from_cedula_natural_person(self):
        self.assertTrue(is_valid_ec_ruc("1711122232001"))
        self.assertFalse(is_valid_ec_ruc("1711122233001"))

    def test_process_text_minimum_viable_case(self):
        result = process_text("Me llamo Esteban Molina, mi cedula es 1711122232 y mi correo es esteban@gmail.com.")

        self.assertEqual(
            result["salida"],
            "Me llamo <PERSONA_1>, mi cedula es <CEDULA_EC_1> y mi correo es <CORREO_1>.",
        )
        entity_types = {entity["tipo"] for entity in result["entidades"]}
        self.assertTrue({"PERSONA", "CEDULA_EC", "CORREO"}.issubset(entity_types))

    def test_preserves_original_positions_when_replacing(self):
        result = process_text("Correo: ana@gmail.com. Telefono: 0998887776.")

        self.assertEqual(result["salida"], "Correo: <CORREO_1>. Telefono: <TELEFONO_EC_1>.")

    def test_evaluates_initial_scenarios(self):
        result = evaluate_scenarios("data/escenarios_iniciales.json")

        self.assertIn("precision", result)
        self.assertIn("exhaustividad", result)
        self.assertGreater(result["indice_exposicion_antes"], result["indice_exposicion_despues"])


if __name__ == "__main__":
    unittest.main()
