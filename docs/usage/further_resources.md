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
The coverage report is generated using [coverage.py](https://coverage.readthedocs.io/en/7.6.1/),
scoped to the `owlapy` package itself (`.coveragerc`) — `examples/`, `setup.py`, and
other non-library scripts are excluded since they aren't part of the installable package.

```
Name                                                               Stmts   Miss  Cover   Missing
------------------------------------------------------------------------------------------------
owlapy/__init__.py                                                     7      0   100%
owlapy/abstracts/__init__.py                                           3      0   100%
owlapy/abstracts/abstract_owl_ontology.py                             14      0   100%
owlapy/abstracts/abstract_owl_reasoner.py                             54     16    70%   390-393, 409-419, 445, 474
owlapy/agen_kg/__init__.py                                             2      0   100%
owlapy/agen_kg/agent.py                                               34      3    91%   4-5, 132
owlapy/agen_kg/chunking_models/__init__.py                             0      0   100%
owlapy/agen_kg/chunking_models/simple_chunker.py                     127      0   100%
owlapy/agen_kg/domain_examples_cache.py                               81      0   100%
owlapy/agen_kg/few_shot_examples.py                                   10      0   100%
owlapy/agen_kg/graph_extracting_models/__init__.py                     3      0   100%
owlapy/agen_kg/graph_extracting_models/domain_graph_extractor.py     235    164    30%   6-7, 202-485
owlapy/agen_kg/graph_extracting_models/open_graph_extractor.py       176     48    73%   6-7, 108-110, 120-122, 150, 152, 171, 182, 202, 212, 219, 227, 236-238, 244, 249, 253, 266, 274, 284, 288-312, 328, 337, 342
owlapy/agen_kg/graph_extractor.py                                    620     33    95%   405, 579, 581, 615, 696, 698, 709, 713-715, 728, 737, 741, 798, 800, 808, 811, 815-817, 830, 839, 843, 901, 946, 998, 1053, 1187, 1246, 1265, 1310, 1361, 1407
owlapy/agen_kg/helper.py                                              34      0   100%
owlapy/agen_kg/signatures.py                                         135      0   100%
owlapy/agen_kg/text_loader.py                                        148      2    99%   153-154
owlapy/class_expression/__init__.py                                    9      0   100%
owlapy/class_expression/class_expression.py                           38      0   100%
owlapy/class_expression/nary_boolean_expression.py                    25      0   100%
owlapy/class_expression/owl_class.py                                  33      0   100%
owlapy/class_expression/restriction.py                               321      5    98%   68-70, 73, 453
owlapy/converter.py                                                  430      9    98%   84, 199, 366, 397, 417, 461, 472, 492, 513
owlapy/entities/__init__.py                                            0      0   100%
owlapy/expressivity.py                                                46     10    78%   59, 66-69, 74, 76, 78, 82, 88
owlapy/iri.py                                                         75      0   100%
owlapy/marked_entity_generator_converter.py                          379      7    98%   190, 220-221, 314, 339, 360, 512
owlapy/meta_classes.py                                                11      0   100%
owlapy/namespaces.py                                                  27      0   100%
owlapy/owl_annotation.py                                              16      0   100%
owlapy/owl_axiom.py                                                  565      4    99%   952, 1234, 1237, 1312
owlapy/owl_data_ranges.py                                              43      0   100%
owlapy/owl_datatype.py                                                22      0   100%
owlapy/owl_hierarchy.py                                              211      8    96%   38, 42, 265-267, 301-303, 351-353
owlapy/owl_individual.py                                               57      2    96%   108, 111
owlapy/owl_literal.py                                                 516     16    97%   281, 452, 701-703, 708, 713, 718, 723, 727, 752, 862, 901, 913, 925, 945
owlapy/owl_object.py                                                   29      0   100%
owlapy/owl_ontology.py                                              1335    303    77%   238-244, 267, 275-278, 382-388, 411-420, 430-436, 444-446, 466, 536, 539, 544-566, 571-588, 592-602, 612-618, 630, 633-634, 674, 679-684, 694, 699, 716, 725-736, 741-756, 767, 772, 782, 794, 798, 834, 840, 851, 857, 862-886, 891-898, 902-921, 940, 953, 992-995, 1010, 1027, 1039, 1043, 1056, 1069, 1085-1086, 1129, 1148-1153, 1159, 1178-1211, 1215, 1218-1220, 1223, 1233, 1262-1263, 1273-1276, 1279, 1285, 1303, 1306, 1309, 1312, 1315, 1323, 1397, 1417, 1435, 1450, 1456, 1655, 1884, 1910-1911, 1934-1935, 2014-2015, 2056, 2060, 2064, 2090, 2197, 2203, 2214-2215, 2219, 2235-2236, 2256, 2261, 2268-2273, 2292-2293, 2312-2316, 2319-2320, 2336-2371, 2376, 2381-2386, 2389, 2394, 2427, 2430
owlapy/owl_property.py                                                 84      1    99%   136
owlapy/owl_reasoner.py                                              1331    337    75%   118, 139, 173, 185-187, 192-198, 203-205, 207-208, 212, 261-267, 273-275, 318-325, 351, 386-390, 416-419, 447-449, 451-453, 482-484, 486-488, 529, 533-534, 570, 631-633, 651-652, 663-667, 670, 700-709, 721, 726, 730, 778-781, 879-883, 901, 918-922, 930-934, 981, 992, 1044, 1067-1077, 1105-1155, 1161-1180, 1184, 1282, 1295, 1305, 1347, 1352-1364, 1377-1381, 1416, 1423-1436, 1522-1524, 1678, 1888-1915, 1946, 2081-2095, 2126, 2130, 2142, 2155-2158, 2164-2188, 2199-2201, 2205-2219, 2263-2277, 2312, 2316, 2328, 2341-2344, 2350-2376, 2387-2389, 2393-2407, 2431, 2437-2438, 2442-2453, 2477-2491, 2617, 2626, 2641, 2652-2653, 2666-2669
owlapy/owl_reasoner_rdflib.py                                        251      8    97%   108-111, 183-186, 297, 374
owlapy/owlapi_dlsyntax.py                                             50      4    92%   36, 189-191
owlapy/owlapi_mapper.py                                              404     26    94%   228, 308, 325-343, 624-632
owlapy/parser.py                                                     390     11    97%   176, 376, 387, 460-461, 475, 721, 732, 816-817, 827
owlapy/providers.py                                                   38      1    97%   56
owlapy/render.py                                                     304     50    84%   102-137, 166-181, 199, 203, 245, 254, 259, 264, 398, 402, 409, 428, 444, 453, 458, 463, 545, 549, 554, 558, 563, 585
owlapy/scripts/__init__.py                                             0      0   100%
owlapy/scripts/litserve_neural_reasoner.py                            22     22     0%   1-80
owlapy/scripts/owlapy_serve.py                                        95     10    89%   53, 59, 121-133
owlapy/scripts/run.py                                                 20     20     0%   1-51
owlapy/static_funcs.py                                                34      0   100%
owlapy/swrl.py                                                       295      8    97%   34, 78-80, 262, 332, 409, 459
owlapy/util_owl_static_funcs.py                                      254     12    95%   337-339, 371, 421, 522-529
owlapy/utils.py                                                     1217    164    87%   390, 404, 493-494, 529, 537, 545, 553, 570, 579, 588, 604, 612, 620, 628, 636, 644-648, 661, 670, 679, 691, 766, 799, 808, 872, 889, 900, 903-910, 913, 996-1009, 1042, 1066, 1070, 1074, 1078, 1120, 1128-1129, 1150, 1176-1178, 1190, 1225, 1233, 1241, 1259, 1281, 1297, 1301, 1305-1311, 1318, 1330-1333, 1339-1340, 1361-1370, 1377-1383, 1392, 1396, 1459, 1469, 1571, 1585-1587, 1638-1639, 1659, 1762, 1814, 1819, 1860, 1865, 1892-1902, 1905-1911, 1914-1925, 1928-1964, 1968-1970, 1975-1979
owlapy/vocab.py                                                      103      0   100%
------------------------------------------------------------------------------------------------
TOTAL                                                              10763   1304    88%
```