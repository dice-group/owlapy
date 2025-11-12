# Further Resources

## Citation

If you use our work in your research, please cite the respective publication:
```
# OWLAPY
@misc{baci2025owlapypythonicframeworkowl,
      title={OWLAPY: A Pythonic Framework for OWL Ontology Engineering}, 
      author={Alkid Baci and Luke Friedrichs and Caglar Demir and Axel-Cyrille Ngonga Ngomo},
      year={2025},
      eprint={2511.08232},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2511.08232}, 
}


# EBR
@misc{teyou2025neuralreasoningrobustinstance,
      title={Neural Reasoning for Robust Instance Retrieval in $\mathcal{SHOIQ}$}, 
      author={Louis Mozart Kamdem Teyou and Luke Friedrichs and N'Dah Jean Kouagou and Caglar Demir and Yasir Mahmood and Stefan Heindorf and Axel-Cyrille Ngonga Ngomo},
      year={2025},
      eprint={2510.20457},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2510.20457}, 
}
```

## More Inside the Project

Examples and test cases provide a good starting point to get to know
the project better. Find them in the folders 
[examples](https://github.com/dice-group/owlapy/tree/develop/examples) and [tests](https://github.com/dice-group/owlapy/tree/develop/tests).

## Contribution

Feel free to create a pull request and we will take a look on it. 
Your commitment is well appreciated!

## Questions

In case you have any question or suggestion, please open an issue on our [GitHub issues page](https://github.com/dice-group/owlapy/issues).

## Coverage Report
The coverage report is generated using [coverage.py](https://coverage.readthedocs.io/en/7.6.1/).

```
Name                                                 Stmts   Miss  Cover   Missing
----------------------------------------------------------------------------------
examples/ontology_justification.py                      49     39    20%   17-73
owlapy/__init__.py                                       5      0   100%
owlapy/abstracts/__init__.py                             3      0   100%
owlapy/abstracts/abstract_owl_ontology.py               14      1    93%   143
owlapy/abstracts/abstract_owl_reasoner.py               49     14    71%   391-394, 409-417, 439, 464
owlapy/class_expression/__init__.py                      9      0   100%
owlapy/class_expression/class_expression.py             38      2    95%   58, 62
owlapy/class_expression/nary_boolean_expression.py      25      0   100%
owlapy/class_expression/owl_class.py                    33      0   100%
owlapy/class_expression/restriction.py                 321     19    94%   41, 49, 66-68, 71, 89, 248-249, 346, 451, 471, 518, 602-603, 641, 776, 824, 860
owlapy/converter.py                                    420    174    59%   52-68, 75-76, 79, 82, 152, 157, 169, 176, 184, 277, 294, 304-307, 313-359, 366-387, 394-401, 417-420, 431, 451, 460-481, 489-491, 498-511, 515-521, 525-548, 552-555, 559-560, 564-576, 580-587, 591-592, 621, 625-629
owlapy/entities/__init__.py                              0      0   100%
owlapy/iri.py                                           75      4    95%   58, 79, 110, 115
owlapy/meta_classes.py                                  11      0   100%
owlapy/namespaces.py                                    27      3    89%   36, 40, 43
owlapy/ontogen/__init__.py                               0      0   100%
owlapy/ontogen/data_extraction.py                      178    178     0%   1-324
owlapy/ontogen/few_shot_examples.py                     10     10     0%   1-102
owlapy/owl_annotation.py                                16      4    75%   16, 24, 42, 50
owlapy/owl_axiom.py                                    545     61    89%   39, 42, 45, 59, 113, 150, 153, 193, 201, 204, 254-257, 265, 289, 295, 298, 301, 339-342, 349, 352, 407-410, 417, 420, 481, 484, 547, 550, 563, 599, 602, 609, 612, 651, 676, 684, 725, 739, 795, 798, 829, 832, 865, 868, 901, 904, 937, 1014, 1105, 1108, 1219, 1222, 1262, 1284, 1288, 1297, 1323
owlapy/owl_data_ranges.py                               40      2    95%   46, 107
owlapy/owl_datatype.py                                  22      0   100%
owlapy/owl_hierarchy.py                                211    211     0%   3-432
owlapy/owl_individual.py                                23      0   100%
owlapy/owl_literal.py                                  516    166    68%   104, 134, 138, 140, 149-170, 181, 190-191, 213, 217, 226, 230, 239, 243, 252, 278, 282, 291, 295, 304, 308, 317, 321, 330, 334, 342, 346, 354, 358, 366, 370, 378, 382, 390, 395, 401, 405, 438, 442, 446-449, 456, 461, 466, 471, 476, 497, 505, 508, 511, 514-516, 532-534, 542, 545, 548, 562, 569-570, 577-578, 585-586, 592-593, 618, 623, 641, 654, 661, 664-666, 669, 682, 687, 698-700, 705, 710, 715, 718-720, 724, 749, 752-755, 765, 781, 784, 794, 797, 806, 809, 812, 819, 822, 825, 838-854, 857-859, 865, 871, 874, 877, 883, 886, 889, 895, 898, 901, 907, 910, 913, 919, 922, 925, 932-934, 937, 940-942, 945
owlapy/owl_object.py                                    29      4    86%   26, 83-85
owlapy/owl_ontology.py                                1168    276    76%   103, 114-117, 120, 128, 145-151, 174, 182-185, 286-292, 315-324, 329-350, 370, 440, 443, 448-470, 475-485, 495-501, 513, 516-517, 557, 562-567, 577, 582, 599, 608-619, 624-639, 650, 655, 665, 677, 681, 717, 723, 734, 740, 745-769, 774-781, 801, 814, 829-830, 853-856, 871, 888, 900, 904, 917, 930, 938-939, 946-947, 952, 961-966, 973, 976-978, 981, 991, 1017-1018, 1027, 1030, 1036, 1054, 1057, 1060, 1063, 1066, 1074, 1120, 1123-1126, 1163, 1182-1183, 1197, 1208, 1426, 1436, 1452-1453, 1476-1477, 1556-1557, 1598, 1602, 1606, 1632, 1739, 1745, 1753, 1757, 1778-1801, 1811-1842, 1845-1850, 1855, 1860-1865, 1868, 1873, 1906, 1909
owlapy/owl_property.py                                  84     13    85%   17, 24, 32, 40, 67, 76, 130, 135, 173, 177, 189, 208, 216
owlapy/owl_reasoner.py                                 907    168    81%   97, 118, 152, 164-166, 171-177, 182-184, 186-187, 191, 240-246, 252-254, 297-304, 330, 365-369, 395-398, 426-428, 430-432, 439-441, 443-444, 448, 461-463, 465-467, 472-474, 476-477, 481, 486-488, 508, 512-513, 526-528, 549, 594-596, 610-612, 630-631, 642-646, 649, 655, 679-688, 700, 705, 709, 757-760, 858-862, 880, 887, 897-901, 909-913, 954-960, 971, 1074-1088, 1174, 1193, 1229-1231, 1294, 1336, 1385, 1400, 1415-1417, 1583-1607, 1638, 1670, 1681-1682, 1695-1698
owlapy/owlapi_mapper.py                                368      8    98%   206, 485-493
owlapy/parser.py                                       371     10    97%   316, 327, 400-401, 416, 656, 667, 751-752, 763
owlapy/providers.py                                     38      3    92%   41, 54, 56
owlapy/render.py                                       305     50    84%   80-115, 144-159, 177, 181, 223, 232, 237, 242, 376, 380, 387, 406, 422, 431, 436, 441, 523, 527, 532, 536, 541, 563
owlapy/scripts/owlapy_serve.py                          95     10    89%   52, 58, 120-132
owlapy/static_funcs.py                                  34     19    44%   22-27, 32-43, 65-67
owlapy/swrl.py                                         295    100    66%   35, 38-40, 43-45, 51-53, 59, 79-81, 96, 108, 114, 122, 126, 133, 136-141, 143-148, 154, 157, 199, 202, 205, 208, 211, 220, 223-225, 237, 240, 243, 246, 249, 258, 261-263, 274, 277, 280, 283, 286, 306, 309-311, 328, 331-333, 341-342, 345, 348, 351, 354, 357, 360, 366, 369-371, 380-381, 384, 387, 390, 393, 396, 399, 405, 408-410, 424, 427, 430, 433, 436, 455, 458-460, 512-514, 517
owlapy/util_owl_static_funcs.py                        254    201    21%   55, 149-209, 214-217, 263-375, 395-421, 441-460, 476-561
owlapy/utils.py                                       1141    304    73%   44-48, 61-74, 82-83, 106-110, 127-138, 281, 285, 289, 295, 301-305, 309-313, 317, 321, 325, 331, 335, 339, 343, 347, 353, 359, 365, 369, 373, 377, 381-384, 388-391, 395, 402, 417-419, 422-431, 434, 437, 440, 443, 446, 450-456, 462-463, 478, 482, 486, 490, 494-498, 502-506, 514, 522, 530, 534-539, 543-548, 552-557, 561, 565, 569-573, 577-581, 585-589, 593-597, 601-605, 609, 613-617, 621, 625-630, 634-639, 643-648, 652, 656-660, 673-674, 735, 768, 777, 841, 858, 869, 872-879, 882, 969-974, 1007, 1031, 1035, 1039, 1043, 1085, 1093-1094, 1115, 1141-1143, 1155, 1190, 1198, 1206, 1224, 1246, 1262, 1266, 1270-1276, 1283, 1295-1298, 1304-1305, 1326-1335, 1342-1348, 1357, 1361, 1424, 1434, 1441, 1536, 1550-1552, 1603-1604, 1624, 1650, 1655, 1696, 1701, 1728-1738, 1741-1747, 1750-1761, 1764-1800, 1804-1806, 1811-1815
owlapy/utils_debug.py                                 1157   1157     0%   2-1839
owlapy/vocab.py                                        103      2    98%   124-125
setup.py                                                13     13     0%   1-53
----------------------------------------------------------------------------------
TOTAL                                                 9002   3226    64%
```