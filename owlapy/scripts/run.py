import argparse
from owlapy.owl_reasoner import SyncReasoner

inference_types = ["InferredClassAssertionAxiomGenerator",
                   "InferredSubClassAxiomGenerator",
                   "InferredDisjointClassesAxiomGenerator",
                   "InferredEquivalentClassAxiomGenerator",
                   "InferredEquivalentDataPropertiesAxiomGenerator",
                   "InferredEquivalentObjectPropertyAxiomGenerator",
                   "InferredInverseObjectPropertiesAxiomGenerator",
                   "InferredSubDataPropertyAxiomGenerator",
                   "InferredSubObjectPropertyAxiomGenerator",
                   "InferredDataPropertyCharacteristicAxiomGenerator",
                   "InferredObjectPropertyCharacteristicAxiomGenerator"]


def get_default_arguments(description=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--path_ontology", type=str, default="KGs/Family/family-benchmark_rich_background.owl",
                        help="The path of a folder containing the ontology"
                             ",e.g., KGs/Family/family-benchmark_rich_background.owl.")
    parser.add_argument("--inference_types", type=str, default="all",
                        nargs='+',
                        choices=inference_types + ["all"],
                        help="The type of axioms that you want to infer. This argument accepts multiple values."
                             "You can use 'all' to infer all of them.")

    parser.add_argument("--out_ontology", type=str, default="inferred_axioms_ontology.owl",
                        help="Path of a file to save the output ontology containing the inferred axioms.")
    parser.add_argument("--output_type", type=str, default=None, choices=["ttl", "rdf/xml", "owl/xml"],
                        help="Filetype of the output ontology.")

    if description is None:
        return parser.parse_args()
    return parser.parse_args(description)


def main():

    args = get_default_arguments()
    sync_reasoner = SyncReasoner(args.path_ontology)
    if args.inference_types is "all":
        it = inference_types
    else:
        it = args.inference_types
    sync_reasoner.infer_axioms_and_save(output_path=args.out_ontology, output_format=args.output_type,
                                        inference_types=it)
    print("Finished inferring axioms \nOutput filename: '{}'".format(args.out_ontology))


if __name__ == '__main__':
    main()
