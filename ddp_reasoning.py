"""
# Terminal 1
ray start --head --port=6379 --num-cpus=1 --resources='{"server_alpha": 1}'
# Terminal 2
ray start --address='192.168.2.225:6379' --num-cpus=1 --resources='{"server_beta": 1}'

# Terminal 3 Client
python ddp_reasoning.py
"""


import ray
from owlapy.owl_reasoner import SyncReasoner
from owlapy.class_expression import OWLClass
from owlapy.vocab import IRI

ray.init(address='auto')

@ray.remote
class DDP_Reasoner:
    def __init__(self, shard_id, ontology_path):
        self.shard_id = shard_id
        # Load data into RAM once
        self.sync_reasoner = SyncReasoner(ontology = ontology_path, reasoner="Pellet")
        print(f"--- Shard {shard_id} initialized and data loaded into RAM ---")

    def query(self, owl_object):
        print(f"Shard {self.shard_id} searching for: {owl_object}")
        return self.sync_reasoner.instances(owl_object,direct=False)
    
if __name__ == "__main__":
    # 1. Instantiate Actors on specific nodes based on resources. TODO: Ensure that datasets are ABOX Fragments of the original data.
    shard_1 = DDP_Reasoner.options(resources={"server_alpha": 1}).remote("Alpha", "/home/cdemir/Desktop/Softwares/owlapy/KGs/Family/family-benchmark_rich_background.owl")
    shard_2 = DDP_Reasoner.options(resources={"server_beta": 1}).remote("Beta", "/home/cdemir/Desktop/Softwares/owlapy/KGs/Family/family-benchmark_rich_background.owl")

    # 2. Perform a distributed search
    query = OWLClass(IRI('http://www.benchmark.org/family#', 'Male'))
    print(f"\nRequesting '{query}' from all shards...")

    # Both shards search their own memory in parallel
    results = ray.get([shard_1.query.remote(query),shard_2.query.remote(query)])
    # 3. Merge results (The 'Reduce' step)
    flat_results = {item for sublist in results for item in sublist}
    print(f"\nFound {len(flat_results)} records:")
    for record in flat_results:
        print(f" - {record}")