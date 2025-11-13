import argparse
import litserve as ls
from owlapy.owl_reasoner import EBR
from owlapy.owl_ontology import NeuralOntology
from owlapy import dl_to_owl_expression
from owlapy import owl_expression_to_dl

class NeuralReasonerAPI(ls.LitAPI):
    """
    NeuralReasonerAPI is a LitAPI implementation that handles requests to a neural reasoner 
    using OWL expressions. It utilizes a neural embedding model for reasoning 
    over ontology data.
    
    Attributes:
        path_neural_embedding (str): Path to the neural embedding.
        gamma (float): Minimum confidence threshold for the reasoning model, defaults to 0.9.
    """
    def __init__(self, path_neural_embedding, gamma=0.9):
        """
        Initializes the NeuralReasonerAPI with the path to the neural embedding and gamma value.
        
        Args:
            path_neural_embedding (str): Path to the neural embedding model.
			gamma (float): Minimum confidence threshold for the reasoning model, defaults to 0.9.
        """
        super().__init__()
        self.path_neural_embedding = path_neural_embedding
        self.gamma = gamma
    
    def setup(self, device):
        """
        Sets up the neural reasoner instance.
        """
        self.neural_owl_reasoner = EBR(NeuralOntology(path_neural_embedding=self.path_neural_embedding,
                                                      gamma=self.gamma))
        
    def decode_request(self, request):
        """
        Decodes an incoming request to extract the DL expression and namespace.
        
        Args:
            request (dict): A dictionary containing the request data, with 'expression' and 'namespace' keys.
        
        Returns:
            tuple: A tuple with the DL expression (str) and namespace (str).
        """
        expression = request["expression"]  
        namespace = request["namespace"]    
        return expression, namespace
        
    def predict(self, data):
        """
        Predicts individuals of the given OWL expression using the neural reasoner.
        
        Args:
            data (tuple): A tuple containing the DL expression (str) and namespace (str).
        
        Returns:
            set: A set of individuals satisfying the given OWL expression.
        """
        expressions, namespace = data
        owl_expression = dl_to_owl_expression(
            namespace=namespace,
            dl_expression=expressions
        )  # Convert DL string to OWLClassExpression
        return set(self.neural_owl_reasoner.individuals(owl_expression))

    def encode_response(self, output):
        """
        Encodes the output from the reasoner back into a DL expression format for response.
        
        Args:
            output (set): A set of OWL expressions representing the individuals.
        
        Returns:
            dict: A dictionary with 'retrieval_result' key containing a list of DL expressions as strings.
        """
        return {'retrieval_result': [owl_expression_to_dl(out) for out in output]}


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Neural Reasoner API")
    parser.add_argument("--path_kge_model", type=str, default="KGs_Family_father_owl",
                        help="Path to the neural embedding folder")
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of model copies for reasoning per device")
    parser.add_argument("--path_kg", type=str, default="KGs/Family/father.owl",
                        help="Path to the ontology file")
    args = parser.parse_args()

    # Initialize API and server
    api = NeuralReasonerAPI(path_neural_embedding=args.path_kge_model)
    server = ls.LitServer(api, accelerator="auto", workers_per_device=args.workers, track_requests=True)
    server.run(port=8000)
