import unittest
import os

from parsimonious.exceptions import IncompleteParseError

from examples.ontology_justification import adjust_namespace
from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLObjectPropertyAssertionAxiom, OWLClassAssertionAxiom, OWLSubClassOfAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy import dl_to_owl_expression, manchester_to_owl_expression
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_reasoner import SyncReasoner


class TestCreateJustifications(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology_path = None
        for root, dirs, files in os.walk("."):
            for file in files:
                if file == "family-benchmark_rich_background.owl":
                    cls.ontology_path = os.path.abspath(os.path.join(root, file))
                    break
            if cls.ontology_path:
                break

        if cls.ontology_path is None:
            raise FileNotFoundError("Could not locate 'family-benchmark_rich_background.owl' within project structure.")

        cls.namespace = adjust_namespace("http://www.benchmark.org/family#")

        try:
            cls.ontology = SyncOntology(cls.ontology_path)
            cls.reasoner = SyncReasoner(cls.ontology, reasoner="Pellet")
        except Exception as e:
            raise RuntimeError(f"Failed to load ontology or initialize reasoner: {e}")

    def test_create_justifications_with_DL_syntax(self):
        individual = OWLNamedIndividual(IRI.create(self.namespace + "F10M171"))
        dl_expr_str = "∃ hasChild.Male"

        target_class = dl_to_owl_expression(dl_expr_str, self.namespace)
        justifications = self.reasoner.create_justifications({individual}, target_class, save=False)

        self.assertIsInstance(justifications, list, "Justifications should be a list.")
        for justification in justifications:
            self.assertIsInstance(justification, set, "Each justification should be a set.")

        # Fake individual
        fake_individual = OWLNamedIndividual(IRI.create(self.namespace + "NonExistentPerson"))
        justifications = self.reasoner.create_justifications({fake_individual}, target_class, save=False)
        self.assertEqual(len(justifications), 0, "Justifications for non-existent individual should be empty.")

        # Invalid DL expression
        with self.assertRaises(IncompleteParseError, msg="Invalid DL expression should raise exception."):
            invalid_expr = dl_to_owl_expression("invalid some Expression", self.namespace)
            self.reasoner.create_justifications(invalid_expr, target_class, save=False)

    def test_create_justifications_with_Fake_Individual_Invalid_DL_syntax(self):
        individual = OWLNamedIndividual(IRI.create(self.namespace + "F10M171"))
        dl_expr_str = "∃ hasChild.Male"
        target_class = dl_to_owl_expression(dl_expr_str, self.namespace)

        # Fake individual
        fake_individual = OWLNamedIndividual(IRI.create(self.namespace + "NonExistentPerson"))
        justifications = self.reasoner.create_justifications({fake_individual}, target_class, save=False)
        self.assertEqual(len(justifications), 0, "Justifications for non-existent individual should be empty.")

        # Invalid DL expression
        with self.assertRaises(IncompleteParseError, msg="Invalid DL expression should raise exception."):
            invalid_expr = dl_to_owl_expression("invalid some Expression", self.namespace)
            self.reasoner.create_justifications(invalid_expr, target_class, save=False)

    def test_create_justifications_with_Manchester_syntax(self):
        individual = OWLNamedIndividual(IRI.create(self.namespace + "F1F2"))
        manchester_expr_str = "hasChild some Female"

        target_class = manchester_to_owl_expression(manchester_expr_str, self.namespace)
        justifications = self.reasoner.create_justifications({individual}, target_class, save=False)
        print(justifications)

        self.assertIsInstance(justifications, list)
        for justification in justifications:
            self.assertIsInstance(justification, set)
        self.assertCountEqual(justifications, [{
            OWLObjectPropertyAssertionAxiom(
                subject=OWLNamedIndividual(IRI('http://www.benchmark.org/family#', 'F1F2')),
                property_=OWLObjectProperty(IRI('http://www.benchmark.org/family#', 'hasChild')),
                object_=OWLNamedIndividual(IRI('http://www.benchmark.org/family#', 'F1F3')),
                annotations=[]), OWLClassAssertionAxiom(
                individual=OWLNamedIndividual(IRI('http://www.benchmark.org/family#', 'F1F3')),
                class_expression=OWLClass(IRI('http://www.benchmark.org/family#', 'Female')),
                annotations=[])}, {OWLObjectPropertyAssertionAxiom(
            subject=OWLNamedIndividual(IRI('http://www.benchmark.org/family#', 'F1F2')),
            property_=OWLObjectProperty(IRI('http://www.benchmark.org/family#', 'hasChild')),
            object_=OWLNamedIndividual(IRI('http://www.benchmark.org/family#', 'F1F3')),
            annotations=[]), OWLClassAssertionAxiom(
            individual=OWLNamedIndividual(IRI('http://www.benchmark.org/family#', 'F1F3')),
            class_expression=OWLClass(IRI('http://www.benchmark.org/family#', 'Mother')),
            annotations=[]), OWLSubClassOfAxiom(
            sub_class=OWLClass(IRI('http://www.benchmark.org/family#', 'Mother')),
            super_class=OWLClass(IRI('http://www.benchmark.org/family#', 'Female')),
            annotations=[])}, {OWLSubClassOfAxiom(
            sub_class=OWLClass(IRI('http://www.benchmark.org/family#', 'Daughter')),
            super_class=OWLClass(IRI('http://www.benchmark.org/family#', 'Female')),
            annotations=[]), OWLObjectPropertyAssertionAxiom(
            subject=OWLNamedIndividual(IRI('http://www.benchmark.org/family#', 'F1F2')),
            property_=OWLObjectProperty(IRI('http://www.benchmark.org/family#', 'hasChild')),
            object_=OWLNamedIndividual(IRI('http://www.benchmark.org/family#', 'F1F3')),
            annotations=[]), OWLClassAssertionAxiom(
            individual=OWLNamedIndividual(IRI('http://www.benchmark.org/family#', 'F1F3')),
            class_expression=OWLClass(IRI('http://www.benchmark.org/family#', 'Daughter')),
            annotations=[])}])

    def test_create_justifications_with_Fake_Individual_Invalid_Manchester_syntax(self):
        individual = OWLNamedIndividual(IRI.create(self.namespace + "F10M171"))
        manchester_expr_str = "hasChild some Male"
        target_class = manchester_to_owl_expression(manchester_expr_str, self.namespace)

        # Fake individual
        fake_individual = OWLNamedIndividual(IRI.create(self.namespace + "Ghost123"))
        justifications = self.reasoner.create_justifications({fake_individual}, target_class, save=False)
        self.assertEqual(len(justifications), 0)

        # Invalid Manchester expression
        invalid_expr = manchester_to_owl_expression("invalid some Expression", self.namespace)
        justifications = self.reasoner.create_justifications({individual}, invalid_expr, save=False)
        self.assertEqual(len(justifications), 0, "Justifications for non-existent individual should be empty.")

    def test_create_justifications_empty_inputs(self):

        with self.assertRaises(ValueError):
            self.reasoner.create_justifications(None, None, save=False)

        with self.assertRaises(ValueError):
            self.reasoner.create_justifications(set(), None, save=False)

    def test_multiple_individuals_and_mixed_results(self):
        valid_individual = OWLNamedIndividual(IRI.create(self.namespace + "F10M171"))
        fake_individual = OWLNamedIndividual(IRI.create(self.namespace + "Ghost"))

        class_expr = dl_to_owl_expression("∃ hasChild.Male", self.namespace)
        justifications = self.reasoner.create_justifications({valid_individual, fake_individual}, class_expr,
                                                             save=False)

        self.assertIsInstance(justifications, list)
        for justification in justifications:
            self.assertIsInstance(justification, set)

    def test_axiom_justification(self):
        F1F3_Daughter = OWLClassAssertionAxiom(
            individual=OWLNamedIndividual(IRI('http://www.benchmark.org/family#', 'F1F3')),
            class_expression=OWLClass(IRI('http://www.benchmark.org/family#', 'Daughter')),
            annotations=[]
        )
        F1F3_Child = OWLClassAssertionAxiom(
            individual=OWLNamedIndividual(IRI('http://www.benchmark.org/family#', 'F1F3')),
            class_expression=OWLClass(IRI('http://www.benchmark.org/family#', 'Child')),
            annotations=[]
        )
        self.assertNotIn(F1F3_Child, set(self.ontology.get_abox_axioms()), "Axiom already present in ontology needs not be justified.")
        try:
            justifications = self.reasoner.create_axiom_justifications(F1F3_Child, None, save=False)
        except Exception as e:
            if not isinstance(e, NotImplementedError):
                raise RuntimeError(f"Unexpected exception during axiom justification: {e}")
        target_justification = {F1F3_Daughter, OWLSubClassOfAxiom(
            sub_class=OWLClass(IRI('http://www.benchmark.org/family#', 'Daughter')),
            super_class=OWLClass(IRI('http://www.benchmark.org/family#', 'Child')),
            annotations=[])}
        for i, justification in enumerate(justifications):
            print(f"Justification {i + 1}:")
            for axiom in justification:
                print(f"  {axiom}")
        # Check that the expected justification is among the generated justifications
        self.assertIn(target_justification, justifications, "Expected justification not found among generated justifications.")


    def test_inconsistency_check(self):
        onto = SyncOntology(IRI.create("KGs/Family/father.owl"))
        ns = "http://example.com/father#"
        male = OWLClass(IRI.create(ns, "male"))
        anna = OWLNamedIndividual(IRI.create(ns, "anna"))
        onto.add_axiom(OWLClassAssertionAxiom(anna, male))

        onto.save("father_inconsistent.owl")

        inconsistent_onto = SyncOntology("father_inconsistent.owl")
        reasoner = SyncReasoner(inconsistent_onto)
        self.assertFalse(reasoner.has_consistent_ontology(), "Ontology with contradictory axioms should be inconsistent.")

        # Check justifications for inconsistency
        justifications = reasoner.create_inconsistency_justifications(n_max_justifications=5)
        self.assertIsInstance(justifications, list, "Justifications should be a list.")
        for justification in justifications:
            self.assertIsInstance(justification, set, "Each justification should be a set.")
            self.assertIn(OWLClassAssertionAxiom(anna, male), justification, "Justification should include the contradictory axiom.")
            print("Inconsistency Justification:")
            for axiom in justification:
                print(f"  {axiom}")

        os.remove("father_inconsistent.owl")

    def test_inconsistency_check_2(self):
        from owlapy.owl_axiom import (
            OWLDisjointClassesAxiom,
            OWLDeclarationAxiom,
            OWLObjectPropertyDomainAxiom,
            OWLObjectPropertyRangeAxiom,
            OWLDifferentIndividualsAxiom
        )
        from owlapy.owl_property import OWLObjectProperty
        from owlapy.class_expression import OWLObjectMaxCardinality
        from owlapy.owl_hierarchy import OWLThing
        default_ns = "http://example.org/ontology#"
        ont = SyncOntology(path=IRI.create(default_ns), load=False)

        # Classes: Car, ElectricCar, GasolineCar, HybridCar
        car = OWLClass(IRI.create(default_ns, "Car"))
        electric_car = OWLClass(IRI.create(default_ns, "ElectricCar"))
        gasoline_car = OWLClass(IRI.create(default_ns, "GasolineCar"))
        hybrid_car = OWLClass(IRI.create(default_ns, "HybridCar"))
        # Declare classes
        ont.add_axiom(OWLDeclarationAxiom(car))
        ont.add_axiom(OWLDeclarationAxiom(electric_car))
        ont.add_axiom(OWLDeclarationAxiom(gasoline_car))
        ont.add_axiom(OWLDeclarationAxiom(hybrid_car))

        # Every ElectricCar is a Car
        # Every GasolineCar is a Car
        ont.add_axiom(OWLSubClassOfAxiom(electric_car, car))
        ont.add_axiom(OWLSubClassOfAxiom(gasoline_car, car))
        # No ElectricCar is a GasolineCar
        ont.add_axiom(OWLDisjointClassesAxiom({electric_car, gasoline_car}))
        # Every HybridCar is an ElectricCar
        ont.add_axiom(OWLSubClassOfAxiom(hybrid_car, electric_car))
        # Every HybridCar is a GasolineCar
        ont.add_axiom(OWLSubClassOfAxiom(hybrid_car, gasoline_car))

        # Every car has at most 4 wheels
        hasWheel = OWLObjectProperty(IRI.create(default_ns, "hasWheel"))
        wheel = OWLClass(IRI.create(default_ns, "Wheel"))
        ont.add_axiom(OWLDeclarationAxiom(hasWheel))
        ont.add_axiom(OWLDeclarationAxiom(wheel))
        ont.add_axiom(OWLObjectPropertyDomainAxiom(hasWheel, car))
        ont.add_axiom(OWLObjectPropertyRangeAxiom(hasWheel, wheel))

        ont.add_axiom(
            OWLSubClassOfAxiom(
                sub_class=car,
                super_class=OWLObjectMaxCardinality(4, hasWheel, wheel)
            )
        )
        
        # If this axiom were added, the reasoner would simply have to justify
        # that owl:Thing is unsatisfiable.
        # ont.add_axiom(OWLSubClassOfAxiom(car, OWLThing))
        # But for some reason, if we do not add it, then the reasoner cannot find any justification.

        # # Make an instance of HybridCar
        # hybrid_car_instance = OWLNamedIndividual(
        #     IRI.create(default_ns, "myHybridCar")
        # )
        # # Declare individual
        # ont.add_axiom(OWLDeclarationAxiom(hybrid_car_instance))
        # ont.add_axiom(OWLClassAssertionAxiom(hybrid_car_instance, hybrid_car))

        # Make a fancy car with 5 wheels
        my_fancy_car = OWLNamedIndividual(IRI.create(default_ns, "myFancyCar"))
        ont.add_axiom(OWLDeclarationAxiom(my_fancy_car))
        for i in range(5):
            ont.add_axiom(OWLDeclarationAxiom(OWLNamedIndividual(IRI.create(default_ns, f"wheel_{i}"))))
            ont.add_axiom(OWLObjectPropertyAssertionAxiom(my_fancy_car, hasWheel, OWLNamedIndividual(IRI.create(default_ns, f"wheel_{i}"))))
        # All wheels are different
        ont.add_axiom(
            OWLDifferentIndividualsAxiom([OWLNamedIndividual(IRI.create(default_ns, f"wheel_{i}")) for i in range(5)])
        )

        # # Show all axioms
        for ax in ont.get_tbox_axioms():
            print(f"Axiom: {ax}")
        for ax in ont.get_abox_axioms():
            print(f"Axiom: {ax}")

        reasoner = SyncReasoner(ont)

        self.assertFalse(reasoner.has_consistent_ontology(), "Ontology with contradictory axioms should be inconsistent.")
        incons_justs = reasoner.create_inconsistency_justifications(
            n_max_justifications=5
        )
        print("\nJustifications for inconsistency:")
        for i, just in enumerate(incons_justs):
            print(f"Inconsistency Justification {i+1}:")
            for ax in just:
                print(f"  {ax}")



if __name__ == "__main__":
    unittest.main()
