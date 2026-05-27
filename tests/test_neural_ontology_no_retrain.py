"""Test that NeuralOntology does not retrain when a model already exists (Issue #161)."""
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch


class TestNeuralOntologyNoRetrain(unittest.TestCase):
    """Test NeuralOntology reuse of existing trained models."""

    def setUp(self):
        """Create temporary directory for test."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_owl_path = os.path.join(self.temp_dir, "test.owl")
        self.model_path = os.path.join(self.temp_dir, "test_trained_model")
        
        # Create a minimal OWL file for testing
        owl_content = """<?xml version="1.0"?>
<rdf:RDF xmlns="http://test.org/onto#"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:owl="http://www.w3.org/2002/07/owl#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
    <owl:Ontology rdf:about="http://test.org/onto"/>
    <owl:Class rdf:about="http://test.org/onto#Person"/>
    <owl:NamedIndividual rdf:about="http://test.org/onto#Alice">
        <rdf:type rdf:resource="http://test.org/onto#Person"/>
    </owl:NamedIndividual>
</rdf:RDF>
"""
        with open(self.test_owl_path, 'w') as f:
            f.write(owl_content)

    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('dicee.executer.Execute')
    @patch('dicee.knowledge_graph_embeddings.KGE')
    def test_no_retrain_when_model_exists(self, mock_kge, mock_execute):
        """Test that Execute is not called when a pretrained model exists."""
        try:
            from owlapy.owl_ontology import NeuralOntology
        except ImportError:
            self.skipTest("dicee package not installed")
        
        # Create a fake pretrained model directory
        os.makedirs(self.model_path, exist_ok=True)
        config_path = os.path.join(self.model_path, "configuration.json")
        with open(config_path, 'w') as f:
            f.write('{"model": "test"}')
        
        # Mock KGE to return a mock model
        mock_model = MagicMock()
        mock_kge.return_value = mock_model
        
        # Create NeuralOntology with train_if_not_exists=True
        # Since model already exists, it should NOT call Execute
        neural_onto = NeuralOntology(
            path_neural_embedding=self.test_owl_path,
            train_if_not_exists=True
        )
        
        # Execute should NOT have been called (model already exists)
        mock_execute.assert_not_called()
        
        # KGE should have been called to load the existing model
        self.assertTrue(mock_kge.called)

    @patch('dicee.executer.Execute')
    @patch('dicee.knowledge_graph_embeddings.KGE')
    def test_train_when_model_does_not_exist(self, mock_kge, mock_execute):
        """Test that Execute is called when no pretrained model exists."""
        try:
            from owlapy.owl_ontology import NeuralOntology
        except ImportError:
            self.skipTest("dicee package not installed")
        
        # Mock Execute and KGE
        mock_execute_instance = MagicMock()
        mock_execute.return_value = mock_execute_instance
        mock_model = MagicMock()
        mock_kge.return_value = mock_model
        
        # Ensure the model directory doesn't exist
        if os.path.exists(self.model_path):
            shutil.rmtree(self.model_path)
        
        # Create the model directory after Execute.start() is called
        def create_model_dir():
            os.makedirs(self.model_path, exist_ok=True)
            config_path = os.path.join(self.model_path, "configuration.json")
            with open(config_path, 'w') as f:
                f.write('{"model": "test"}')
        
        mock_execute_instance.start.side_effect = create_model_dir
        
        # Create NeuralOntology with train_if_not_exists=True
        # Since model doesn't exist, it SHOULD call Execute
        neural_onto = NeuralOntology(
            path_neural_embedding=self.test_owl_path,
            train_if_not_exists=True
        )
        
        # Execute should have been called (new training)
        mock_execute.assert_called_once()
        mock_execute_instance.start.assert_called_once()
        
        # KGE should have been called to load the newly trained model
        self.assertTrue(mock_kge.called)


if __name__ == '__main__':
    unittest.main()
