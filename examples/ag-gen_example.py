from owlapy.agen_kg import AGenKG

filep = "doctors_notes.txt"
# You can use GitHub's hosted models by providing your GitHub Personal Access Token (PAT)
# but you can use any model & API base of you choice.
agent = AGenKG(model="gpt-4o", api_key="<YOUR_GITHUB_PAT>",
             api_base="https://models.github.ai/inference",
             temperature=0.1, seed=42, max_tokens=6000, enable_logging=True)
agent.generate_ontology(text=filep,
                        ontology_type="domain",
                        query="I want the resulting graph to represent medical information "
                              "about each patient from the provided doctors' notes.",
                        generate_types=True,
                        extract_spl_triples=True,
                        create_class_hierarchy=False,
                        fact_reassurance=False,
                        save_path="patients.owl")
