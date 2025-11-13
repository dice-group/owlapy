from owlapy import dl_to_owl_expression, owl_expression_to_dl
from owlapy.utils import simplify_class_expression, get_expression_length

ce_dl = "((((((((((¬Father) ⊓ (¬(∃ hasChild.Grandfather))) ⊓ (¬(∃ hasParent.{F1F2}))) ⊓ (¬(∃ hasSibling.Granddaughter))) \
⊓ Grandson) ⊓ (¬(∃ hasParent.{F8M136}))) ⊔ ((((((¬Father) ⊓ (¬(∃ hasChild.Grandfather))) ⊓ (¬(∃ hasParent.{F1F2}))) ⊓ \
(¬(∃ hasSibling.Granddaughter))) ⊓ (¬Grandson)) ⊓ (∃ married.{F10F179}))) ⊔ (((((¬Father) ⊓ (¬(∃ hasChild.Grandfather))) \
⊓ (¬(∃ hasParent.{F1F2}))) ⊓ (∃ hasSibling.Granddaughter)) ⊓ (¬Grandson))) ⊔ ((¬Father) ⊓ (∃ hasChild.Grandfather))) ⊔ \
(((¬Father) ⊓ (¬(∃ hasChild.Grandfather))) ⊓ (∃ hasParent.{F1F2}))) ⊔ (((Father ⊓ (¬(∃ hasSibling.Grandson))) ⊓ \
(¬(∃ hasChild.{F5M64}))) ⊓ (¬(∃ married.{F2F15})))"
ce_owl = dl_to_owl_expression(ce_dl, "http://www.benchmark.org/family#")
simplified_ce = simplify_class_expression(ce_owl)
print(owl_expression_to_dl(simplified_ce))
print(f"Original CE length: {get_expression_length(ce_owl)} \nSimplified CE length: {get_expression_length(simplified_ce)}")