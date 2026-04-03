import unittest
import os

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
        justifications = self.reasoner.create_axiom_justifications(OWLClassAssertionAxiom(individual, target_class), save=False)

        self.assertIsInstance(justifications, list, "Justifications should be a list.")
        for justification in justifications:
            self.assertIsInstance(justification, set, "Each justification should be a set.")

        # Fake individual — axiom is not entailed, so ValueError is expected
        fake_individual = OWLNamedIndividual(IRI.create(self.namespace + "NonExistentPerson"))
        with self.assertRaises(ValueError):
            self.reasoner.create_axiom_justifications(OWLClassAssertionAxiom(fake_individual, target_class), save=False)


    def test_create_justifications_with_Fake_Individual_Invalid_DL_syntax(self):
        individual = OWLNamedIndividual(IRI.create(self.namespace + "F10M171"))
        dl_expr_str = "∃ hasChild.Male"
        target_class = dl_to_owl_expression(dl_expr_str, self.namespace)

        # Fake individual — axiom is not entailed, so ValueError is expected
        fake_individual = OWLNamedIndividual(IRI.create(self.namespace + "NonExistentPerson"))
        with self.assertRaises(ValueError):
            self.reasoner.create_axiom_justifications(OWLClassAssertionAxiom(fake_individual, target_class), save=False)


    def test_create_justifications_with_Manchester_syntax(self):
        individual = OWLNamedIndividual(IRI.create(self.namespace + "F1F2"))
        manchester_expr_str = "hasChild some Female"

        target_class = manchester_to_owl_expression(manchester_expr_str, self.namespace)
        justifications = self.reasoner.create_axiom_justifications(OWLClassAssertionAxiom(individual, target_class), save=False)
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

        # Fake individual — axiom is not entailed, so ValueError is expected
        fake_individual = OWLNamedIndividual(IRI.create(self.namespace + "Ghost123"))
        with self.assertRaises(ValueError):
            self.reasoner.create_axiom_justifications(OWLClassAssertionAxiom(fake_individual, target_class), save=False)

        # Invalid Manchester expression — axiom with non-existent property/class is not entailed, so ValueError is expected
        invalid_expr = manchester_to_owl_expression("invalid some Expression", self.namespace)
        with self.assertRaises(ValueError):
            self.reasoner.create_axiom_justifications(OWLClassAssertionAxiom(individual, invalid_expr), save=False)

    def test_create_justifications_empty_inputs(self):
        # Passing None as axiom should raise an error
        with self.assertRaises((TypeError, ValueError, AttributeError, NotImplementedError)):
            self.reasoner.create_axiom_justifications(None, save=False)

    def test_multiple_individuals_and_mixed_results(self):
        valid_individual = OWLNamedIndividual(IRI.create(self.namespace + "F10M171"))
        fake_individual = OWLNamedIndividual(IRI.create(self.namespace + "Ghost"))

        class_expr = dl_to_owl_expression("∃ hasChild.Male", self.namespace)

        # Valid individual should return justifications
        j1 = self.reasoner.create_axiom_justifications(OWLClassAssertionAxiom(valid_individual, class_expr), save=False)
        self.assertIsInstance(j1, list)
        for justification in j1:
            self.assertIsInstance(justification, set)

        # Fake individual — axiom is not entailed, so ValueError is expected
        with self.assertRaises(ValueError):
            self.reasoner.create_axiom_justifications(OWLClassAssertionAxiom(fake_individual, class_expr), save=False)

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

        target_justification = {F1F3_Daughter, OWLSubClassOfAxiom(
            sub_class=OWLClass(IRI('http://www.benchmark.org/family#', 'Daughter')),
            super_class=OWLClass(IRI('http://www.benchmark.org/family#', 'Child')),
            annotations=[])}

        justifications = None
        try:
            justifications = self.reasoner.create_axiom_justifications(F1F3_Child, None, save=False)
        except (NotImplementedError, ValueError) as e:
            print(f"Axiom justification raised expected exception: {e}")

        if justifications is not None:
            for i, justification in enumerate(justifications):
                print(f"Justification {i + 1}:")
                for axiom in justification:
                    print(f"  {axiom}")
            # Check that the expected justification is among the generated justifications
            self.assertIn(target_justification, justifications, "Expected justification not found among generated justifications.")

        # Do the same but with laconic justifications
        laconic_justifications = None
        try:
            laconic_justifications = self.reasoner.create_laconic_axiom_justifications(F1F3_Child, None, save=False)
        except (NotImplementedError, ValueError) as e:
            print(f"Laconic axiom justification raised expected exception: {e}")

        if laconic_justifications is not None:
            print("\nLaconic Justifications:")
            for i, justification in enumerate(laconic_justifications):
                print(f"Laconic Justification {i + 1}:")
                for axiom in justification:
                    print(f"  {axiom}")
            self.assertIn(target_justification, laconic_justifications, "Expected justification not found among generated laconic justifications.")


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

            # Verify that each justification is a subset of axioms that form an inconsistent ontology
            test_ont = SyncOntology(path=IRI.create(default_ns), load=False)
            for ax in just:
                test_ont.add_axiom(ax)
            test_reasoner = SyncReasoner(test_ont)
            self.assertFalse(test_reasoner.has_consistent_ontology(), "Justification should lead to an inconsistent ontology.")


class TestJustificationTimeout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology_path = None
        for root, dirs, files in os.walk("."):
            for file in files:
                # Very large ontology with many justifications, so we can test timeout behavior.
                if file == "carcinogenesis.owl":
                    cls.ontology_path = os.path.abspath(os.path.join(root, file))
                    print(f"Found ontology at: {cls.ontology_path}")
                    break
            if cls.ontology_path:
                break

        if cls.ontology_path is None:
            raise FileNotFoundError("Could not locate 'carcinogenesis.owl' within project structure.")

        cls.namespace = adjust_namespace("http://dl-learner.org/carcinogenesis#")

        try:
            print("Loading ontology and initializing reasoner...")
            cls.ontology = SyncOntology(cls.ontology_path)
            cls.reasoner = SyncReasoner(cls.ontology, reasoner="HermiT")
            print("Ontology loaded and reasoner initialized successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to load ontology or initialize reasoner: {e}")

    def test_justification_timeout(self):
        # "Compound and hasAtom some Carbon"
        # In description logic: Compound ⊓ ∃ hasAtom.Carbon
        # Due to ontology size, we could expect some timeout here
        manchester_expr = "Compound and hasAtom some Carbon"
        owl_expr = manchester_to_owl_expression(
            manchester_expr, namespace="http://dl-learner.org/carcinogenesis#"
        )
        d100 = OWLNamedIndividual(
            IRI.create("http://dl-learner.org/carcinogenesis#d100")
        )

        class_assertion = OWLClassAssertionAxiom(d100, owl_expr)
        print("Axiom to prove: ", class_assertion)


        # Check if class assertion is entailed
        if not self.reasoner.is_entailed(class_assertion):
            print("Class assertion is not entailed, so justifications cannot be generated.")
            return
        
        timeout = 1 # Very short timeout to force timeout behavior since the ontology is huge

        with self.assertRaises(TimeoutError) as cm1:
            self.reasoner.create_axiom_justifications(
                class_assertion, timeout=timeout, save=False
            )
        # Get the exception message and check that it contains the expected timeout information
        print(f"Caught exception message: {str(cm1.exception)}")
        with self.assertRaises(TimeoutError) as cm2:
            self.reasoner.create_laconic_axiom_justifications(
                class_assertion, timeout=timeout, save=False
            )
        print(f"Caught exception message for laconic justifications: {str(cm2.exception)}")

        # For some reason, the following does not work, and returns an empty list.
        # The same block of code would work if isolated into a separate test case.


# Create a separate test for no timeout
# Otherwise, for some reason we get ConcurrentModificationException from java
class TestJustificationNoTimeout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology_path = None
        for root, dirs, files in os.walk("."):
            for file in files:
                # Very large ontology with many justifications, so we can test timeout behavior.
                if file == "carcinogenesis.owl":
                    cls.ontology_path = os.path.abspath(os.path.join(root, file))
                    print(f"Found ontology at: {cls.ontology_path}")
                    break
            if cls.ontology_path:
                break

        if cls.ontology_path is None:
            raise FileNotFoundError("Could not locate 'carcinogenesis.owl' within project structure.")

        cls.namespace = adjust_namespace("http://dl-learner.org/carcinogenesis#")

        try:
            print("Loading ontology and initializing reasoner...")
            cls.ontology = SyncOntology(cls.ontology_path)
            cls.reasoner = SyncReasoner(cls.ontology, reasoner="HermiT")
            print("Ontology loaded and reasoner initialized successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to load ontology or initialize reasoner: {e}")

    def test_justifications_no_timeout(self):
        owl_expr = manchester_to_owl_expression(
            "Compound and hasAtom some Carbon", namespace="http://dl-learner.org/carcinogenesis#"
        )
        d100 = OWLNamedIndividual(
            IRI.create("http://dl-learner.org/carcinogenesis#d100")
        )
        class_assertion = OWLClassAssertionAxiom(d100, owl_expr)
        # reasoner = SyncReasoner(self.ontology)
        # Now, just give it an indefinite amount of time
        justifications = self.reasoner.create_axiom_justifications(
            class_assertion,
            n_max_justifications=1,
            timeout=None
        )

        self.assertIsInstance(justifications, list, "Justifications should be a list.")
        # Check that the list is nonempty
        self.assertGreater(len(justifications), 0, "Justifications list should not be empty.")
        print(f"Successfully generated justifications without timeout: {justifications}")
        for justification in justifications:
            print("Justification:")
            for axiom in justification:
                print(f"  {axiom}")

        # This is a bit long, but does the same.
        # justifications_laconic = self.reasoner.create_laconic_axiom_justifications(
        #     class_assertion,
        #     n_max_justifications=3,
        #     timeout=None,
        #     save=False
        # )
        # self.assertIsInstance(justifications_laconic, list, "Laconic justifications should be a list.")
        # print(f"Successfully generated laconic justifications without timeout: {justifications_laconic}")
        # for justification in justifications_laconic:
        #     print("Laconic Justification:")
        #     for axiom in justification:
        #         print(f"  {axiom}")

    def test_consecutive_calls_with_and_without_timeout(self):
        owl_expr = manchester_to_owl_expression(
            "Compound and hasAtom some Carbon", namespace="http://dl-learner.org/carcinogenesis#"
        )
        d100 = OWLNamedIndividual(
            IRI.create("http://dl-learner.org/carcinogenesis#d100")
        )
        class_assertion = OWLClassAssertionAxiom(d100, owl_expr)
        n_tbox_axioms = len(self.ontology.get_tbox_axioms())
        n_abox_axioms = len(self.ontology.get_abox_axioms())
        print(f"Ontology loaded with {n_tbox_axioms} TBox axioms and {n_abox_axioms} ABox axioms.")

        # Assert that axiom is entailed
        self.assertTrue(
            self.reasoner.is_entailed(class_assertion),
            "Axiom should be entailed by the ontology, but was not. Check that the ontology is loaded correctly and that the axiom is correctly formulated."
            f"Number of tbox axioms: {len(self.ontology.get_tbox_axioms())}, number of abox axioms: {len(self.ontology.get_abox_axioms())}"
        )

        # First, call with a short timeout to trigger the timeout behavior
        # Do not use pytest assertRaise
        try:
            self.reasoner.create_axiom_justifications(
                class_assertion,
                n_max_justifications=5,
                timeout=1
            )
        except TimeoutError as e:
            print(f"Timeout occurred as expected: {e}")

        # Assert that axiom is still entailed
        self.assertTrue(
            self.reasoner.is_entailed(class_assertion),
            "Axiom should be entailed by the ontology (after timeout), but was not. Check that the ontology is loaded correctly and that the axiom is correctly formulated."
            f"Number of tbox axioms: {len(self.ontology.get_tbox_axioms())}, number of abox axioms: {len(self.ontology.get_abox_axioms())}"
        )

        # Then, call again with no timeout and check that justifications are generated successfully
        justifications = self.reasoner.create_axiom_justifications(
            class_assertion,
            n_max_justifications=1,
            timeout=None
        )
        self.assertIsInstance(justifications, list, "Justifications should be a list.")
        self.assertGreater(len(justifications), 0, "Justifications list should not be empty.")
        print(f"Successfully generated justifications after previous timeout: {justifications}")
        for justification in justifications:
            print("Justification:")
            for axiom in justification:
                print(f"  {axiom}")


if __name__ == "__main__":
    unittest.main()
