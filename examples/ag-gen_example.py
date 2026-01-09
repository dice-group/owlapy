from owlapy.agen_kg import AGenKG
from owlapy.owl_ontology import SyncOntology

filep = "doctors_notes.txt"
# This example is set up to use GitHub's Models by providing your
# GitHub Personal Access Token (PAT) because it's for free (subject to change),
# but of course, you can use any model & API base of your choice.
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

# === Logs ===
# DomainGraphExtractor: INFO :: Decomposed the query into specific instructions
# UniversalTextLoader: INFO :: Loading text from .txt file: doctors_notes.txt
# UniversalTextLoader: INFO :: Successfully loaded 564 words (4257 characters)
# DomainGraphExtractor: INFO :: Text will be processed in 1 chunks
# DomainGraphExtractor: INFO :: Total chars: 4257, Est. tokens: 1064
# DomainGraphExtractor: INFO :: Detected domain: medicine
# DomainGraphExtractor: INFO :: Generating domain-specific few-shot examples for domain: medicine
# DomainGraphExtractor: INFO :: Generated examples for entity_extraction
# DomainGraphExtractor: INFO :: Generated examples for triples_extraction
# DomainGraphExtractor: INFO :: Generated examples for type_assertion
# DomainGraphExtractor: INFO :: Generated examples for type_generation
# DomainGraphExtractor: INFO :: Generated examples for literal_extraction
# DomainGraphExtractor: INFO :: Generated examples for triples_with_numeric_literals_extraction
# DomainGraphExtractor: INFO :: Cached examples for domain 'medicine' to path_hidden/domain_examples_medicine.json
# DomainGraphExtractor: INFO :: Generated the following entities: ['P001', 'EARLY HYPERTENSION', 'ACE INHIBITORS', 'P002', 'TYPE 2 DIABETES', 'METFORMIN', 'P003', 'SEASONAL FLU', 'ANTIVIRALS', 'P004', 'MECHANICAL BACK PAIN', 'NSAIDS', 'PHYSIOTHERAPY', 'P005', 'MIGRAINES', 'TRIPTANS', 'P006', 'OSTEOARTHRITIS', 'PAIN MANAGEMENT PLAN', 'P007', 'GERD', 'PPIs', 'P008', 'ANXIETY DISORDER', 'CBT', 'SSRIs', 'P009', 'HYPERLIPIDEMIA', 'STATINS', 'P010', 'ASTHMA', 'INHALED BRONCHODILATOR', 'P011', 'COPD', 'BRONCHODILATORS', 'P012', 'IRON DEFICIENCY ANEMIA', 'IRON SUPPLEMENTS', 'P013', 'DEPRESSION', 'ANTIDEPRESSANTS', 'P014', 'IBS', 'DIETARY MODIFICATIONS', 'P015', 'CATARACTS', 'SURGICAL EVALUATION', 'P016', 'HYPOTHYROIDISM', 'LEVOTHYROXINE', 'P017', 'ACUTE PHARYNGITIS', 'ANTIBIOTICS', 'P018', 'RHEUMATOID ARTHRITIS', 'DMARDs', 'P019', 'KIDNEY STONES', 'PAIN RELIEF', 'HYDRATION', 'P020', 'LOW VITAMIN D LEVELS', 'SUPPLEMENTS']
# DomainGraphExtractor: INFO :: Generated the following triples: [('P001', 'HAS', 'EARLY HYPERTENSION'), ('EARLY HYPERTENSION', 'TREATED WITH', 'ACE INHIBITORS'), ('P001', 'PRESCRIBED', 'ACE INHIBITORS'), ('P002', 'HAS', 'TYPE 2 DIABETES'), ('TYPE 2 DIABETES', 'TREATED WITH', 'METFORMIN'), ('P002', 'PRESCRIBED', 'METFORMIN'), ('P003', 'HAS', 'SEASONAL FLU'), ('SEASONAL FLU', 'TREATED WITH', 'ANTIVIRALS'), ('P003', 'PRESCRIBED', 'ANTIVIRALS'), ('P004', 'HAS', 'MECHANICAL BACK PAIN'), ('MECHANICAL BACK PAIN', 'TREATED WITH', 'NSAIDS'), ('P004', 'PRESCRIBED', 'NSAIDS'), ('P004', 'REFERRED TO', 'PHYSIOTHERAPY'), ('P005', 'HAS', 'MIGRAINES'), ('MIGRAINES', 'TREATED WITH', 'TRIPTANS'), ('P005', 'PRESCRIBED', 'TRIPTANS'), ('P006', 'HAS', 'OSTEOARTHRITIS'), ('OSTEOARTHRITIS', 'TREATED WITH', 'PAIN MANAGEMENT PLAN'), ('P007', 'HAS', 'GERD'), ('GERD', 'TREATED WITH', 'PPIs'), ('P007', 'PRESCRIBED', 'PPIs'), ('P008', 'HAS', 'ANXIETY DISORDER'), ('ANXIETY DISORDER', 'TREATED WITH', 'CBT'), ('ANXIETY DISORDER', 'TREATED WITH', 'SSRIs'), ('P008', 'PRESCRIBED', 'SSRIs'), ('P009', 'HAS', 'HYPERLIPIDEMIA'), ('HYPERLIPIDEMIA', 'TREATED WITH', 'STATINS'), ('P009', 'PRESCRIBED', 'STATINS'), ('P010', 'HAS', 'ASTHMA'), ('ASTHMA', 'TREATED WITH', 'INHALED BRONCHODILATOR'), ('P010', 'PRESCRIBED', 'INHALED BRONCHODILATOR'), ('P011', 'HAS', 'COPD'), ('COPD', 'TREATED WITH', 'BRONCHODILATORS'), ('P011', 'PRESCRIBED', 'BRONCHODILATORS'), ('P012', 'HAS', 'IRON DEFICIENCY ANEMIA'), ('IRON DEFICIENCY ANEMIA', 'TREATED WITH', 'IRON SUPPLEMENTS'), ('P012', 'PRESCRIBED', 'IRON SUPPLEMENTS'), ('P013', 'HAS', 'DEPRESSION'), ('DEPRESSION', 'TREATED WITH', 'ANTIDEPRESSANTS'), ('P013', 'PRESCRIBED', 'ANTIDEPRESSANTS'), ('P014', 'HAS', 'IBS'), ('IBS', 'TREATED WITH', 'DIETARY MODIFICATIONS'), ('P015', 'HAS', 'CATARACTS'), ('CATARACTS', 'TREATED WITH', 'SURGICAL EVALUATION'), ('P016', 'HAS', 'HYPOTHYROIDISM'), ('HYPOTHYROIDISM', 'TREATED WITH', 'LEVOTHYROXINE'), ('P016', 'PRESCRIBED', 'LEVOTHYROXINE'), ('P017', 'HAS', 'ACUTE PHARYNGITIS'), ('ACUTE PHARYNGITIS', 'TREATED WITH', 'ANTIBIOTICS'), ('P017', 'PRESCRIBED', 'ANTIBIOTICS'), ('P018', 'HAS', 'RHEUMATOID ARTHRITIS'), ('RHEUMATOID ARTHRITIS', 'TREATED WITH', 'DMARDs'), ('P018', 'PRESCRIBED', 'DMARDs'), ('P019', 'HAS', 'KIDNEY STONES'), ('KIDNEY STONES', 'TREATED WITH', 'PAIN RELIEF'), ('KIDNEY STONES', 'TREATED WITH', 'HYDRATION'), ('P020', 'HAS', 'LOW VITAMIN D LEVELS'), ('LOW VITAMIN D LEVELS', 'TREATED WITH', 'SUPPLEMENTS')]
# DomainGraphExtractor: INFO :: Using summary (3000 chars) for relation clustering
# DomainGraphExtractor: INFO :: Merged 1 duplicate relations
# DomainGraphExtractor: INFO :: After relation clustering: ['TREATED WITH', 'HAS', 'REFERRED TO']
# DomainGraphExtractor: INFO :: Skipped coherence check, using all 58 triples
# DomainGraphExtractor: INFO :: Finished generating types and assigned them to entities as following: [('P001', 'Patient'), ('EARLY HYPERTENSION', 'MedicalCondition'), ('ACE INHIBITORS', 'Medication'), ('P002', 'Patient'), ('TYPE 2 DIABETES', 'MedicalCondition'), ('METFORMIN', 'Medication'), ('P003', 'Patient'), ('SEASONAL FLU', 'MedicalCondition'), ('ANTIVIRALS', 'Medication'), ('P004', 'Patient'), ('MECHANICAL BACK PAIN', 'MedicalCondition'), ('NSAIDS', 'Medication'), ('PHYSIOTHERAPY', 'Procedure'), ('P005', 'Patient'), ('MIGRAINES', 'MedicalCondition'), ('TRIPTANS', 'Medication'), ('P006', 'Patient'), ('OSTEOARTHRITIS', 'MedicalCondition'), ('PAIN MANAGEMENT PLAN', 'Procedure'), ('P007', 'Patient'), ('GERD', 'MedicalCondition'), ('PPIs', 'Medication'), ('P008', 'Patient'), ('ANXIETY DISORDER', 'MedicalCondition'), ('CBT', 'Procedure'), ('SSRIs', 'Medication'), ('P009', 'Patient'), ('HYPERLIPIDEMIA', 'MedicalCondition'), ('STATINS', 'Medication'), ('P010', 'Patient'), ('ASTHMA', 'MedicalCondition'), ('INHALED BRONCHODILATOR', 'Medication'), ('P011', 'Patient'), ('COPD', 'MedicalCondition'), ('BRONCHODILATORS', 'Medication'), ('P012', 'Patient'), ('IRON DEFICIENCY ANEMIA', 'MedicalCondition'), ('IRON SUPPLEMENTS', 'Medication'), ('P013', 'Patient'), ('DEPRESSION', 'MedicalCondition'), ('ANTIDEPRESSANTS', 'Medication'), ('P014', 'Patient'), ('IBS', 'MedicalCondition'), ('DIETARY MODIFICATIONS', 'Procedure'), ('P015', 'Patient'), ('CATARACTS', 'MedicalCondition'), ('SURGICAL EVALUATION', 'Procedure'), ('P016', 'Patient'), ('HYPOTHYROIDISM', 'MedicalCondition'), ('LEVOTHYROXINE', 'Medication'), ('P017', 'Patient'), ('ACUTE PHARYNGITIS', 'MedicalCondition'), ('ANTIBIOTICS', 'Medication'), ('P018', 'Patient'), ('RHEUMATOID ARTHRITIS', 'MedicalCondition'), ('DMARDs', 'Medication'), ('P019', 'Patient'), ('KIDNEY STONES', 'MedicalCondition'), ('PAIN RELIEF', 'Procedure'), ('HYDRATION', 'Procedure'), ('P020', 'Patient'), ('LOW VITAMIN D LEVELS', 'LabResult'), ('SUPPLEMENTS', 'Medication')]
# DomainGraphExtractor: INFO :: Generated the following numeric literals: ['34', '58', '22', '45', '29', '67', '41', '36', '50', '19', '62', '27', '48', '33', '71', '39', '24', '55', '46', '31', '1']
# DomainGraphExtractor: INFO :: Generated the following s-p-l triples: [('P001', 'AGE', '34'), ('P002', 'AGE', '58'), ('P003', 'AGE', '22'), ('P004', 'AGE', '45'), ('P005', 'AGE', '29'), ('P006', 'AGE', '67'), ('P007', 'AGE', '41'), ('P008', 'AGE', '36'), ('P009', 'AGE', '50'), ('P010', 'AGE', '19'), ('P011', 'AGE', '62'), ('P012', 'AGE', '27'), ('P013', 'AGE', '48'), ('P014', 'AGE', '33'), ('P015', 'AGE', '71'), ('P016', 'AGE', '39'), ('P017', 'AGE', '24'), ('P018', 'AGE', '55'), ('P019', 'AGE', '46'), ('P020', 'AGE', '31')]
# Saving patients.owl..

# You can load the generated ontology and work with it as normally
onto = SyncOntology(path="patients.owl")
[print(ax) for ax in onto.get_abox_axioms()]
[print(ax) for ax in onto.get_tbox_axioms()]
