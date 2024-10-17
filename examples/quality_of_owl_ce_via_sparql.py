"""
The confusion matrix indicating the quality of an OWL Class Expression can be computed through SPARQL.
By this, we avoid the process of retrieving instances of an OWL Class Expression, hence, accelerate the learning process
"""
from owlapy import owl_expression_to_sparql_with_confusion_matrix
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.class_expression import OWLClass
import requests

pos={OWLNamedIndividual('http://dbpedia.org/resource/George_Montagu_(naturalist)'), OWLNamedIndividual('http://dbpedia.org/resource/Andrei_Monin'), OWLNamedIndividual('http://dbpedia.org/resource/Joe_Bastardi')}
neg={OWLNamedIndividual('http://dbpedia.org/resource/James_M._Bower'), OWLNamedIndividual('http://dbpedia.org/resource/Shirley_Meng'), OWLNamedIndividual('http://dbpedia.org/resource/Betsy_Weatherhead')}
response = requests.post("https://dbpedia-2022-12.data.dice-research.org/sparql", data={"query": owl_expression_to_sparql_with_confusion_matrix(expression=OWLClass('http://dbpedia.org/ontology/Person'),positive_examples=pos,negative_examples=neg)})
for res in response.json()["results"]["bindings"]:
    for k,v in res.items():
        print(k,eval(v["value"]))


"""
tp 3.0
fn 0.0
fp 3.0
tn 0.0
"""