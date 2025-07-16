from owlapy.ontogen.data_extraction import get_entities, GraphExtractor, assign_types

text_example_1 = """NeoChip’s (NC) shares surged in their first week of trading on the NewTech Exchange. 
However, market analysts caution that the chipmaker’s public debut may not reflect trends for other technology IPOs. 
NeoChip, previously a private entity, was acquired by Quantum Systems in 2016. The innovative semiconductor firm
specializes in low-power processors for wearables and IoT devices."""

text_example_2 = """In an interview from the Oval Office, president Trump also endorsed Nato, having once described it 
as obsolete, and affirmed his support for the organisation's common defence principle. The president made the phone call, 
which lasted 20 minutes, to the BBC after conversations about a potential interview to mark one year on since the attempt 
on his life at a campaign rally in Butler, Pennsylvania."""

text_example_3 = """J.P. Morgan & Co. is an American financial institution specialized in investment banking, 
asset management and private banking founded by financier J. P. Morgan in 1871. Through a series of mergers and 
acquisitions, the company is now a subsidiary of JPMorgan Chase, the largest banking institution in the world. 
The company has been historically referred to as the "House of Morgan" or simply Morgan."""

entity_types = ["ORGANIZATION", "PERSON"]

# print(get_entities(text_example_1))
# print(get_entities(text_example_2))
# print(get_entities(text_example_3))

ontogen = GraphExtractor(model="Qwen/Qwen3-32B-AWQ",api_key="", api_base="http://tentris-ml.cs.upb.de:8501/v1",
                         temperature=0.1, seed=42)

ontogen(text=text_example_3, entity_types=entity_types) # creates generated_ontology.owl in the current directory
