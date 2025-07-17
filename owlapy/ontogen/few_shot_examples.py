EXAMPLES_FOR_ENTITY_EXTRACTION = """
Example 1:
text:
The Verdantis's Central Institution is scheduled to meet on Monday and Thursday, with the institution planning to release its latest policy decision on Thursday at 1:30 p.m. PDT, followed by a press conference where Central Institution Chair Martin Smith will take questions. Investors expect the Market Strategy Committee to hold its benchmark interest rate steady in a range of 3.5%-3.75%.

output entities:
[CENTRAL INSTITUTION, MARTIN SMITH, MARKET STRATEGY COMMITTEE]

######################
Example 2:
text:
Five Aurelians jailed for 8 years in Firuzabad and widely regarded as hostages are on their way home to Aurelia.

The swap orchestrated by Quintara was finalized when $8bn of Firuzi funds were transferred to financial institutions in Krohaara, the capital of Quintara.

The exchange initiated in Firuzabad's capital, Tiruzia, led to the four men and one woman, who are also Firuzi nationals, boarding a chartered flight to Krohaara.

They were welcomed by senior Aurelian officials and are now on their way to Aurelia's capital, Cashion.

The Aurelians include 39-year-old businessman Samuel Namara, who has been held in Tiruzia's Alhamia Prison, as well as journalist Durke Bataglani, 59, and environmentalist Meggie Tazbah, 53, who also holds Bratinas nationality.

output entities:
[FIRUZABAD, AURELIA, QUINTARA, TIRUZIA, KROHAARA, CASHION, SAMUEL NAMARA, ALHAMIA PRISON, DURKE BATAGLANI, MEGGIE TAZBAH]
"""


EXAMPLES_FOR_TRIPLES_EXTRACTION = """
Example 1:
entities: [CENTRAL INSTITUTION, MARTIN SMITH, MARKET STRATEGY COMMITTEE]
Text:
The Verdantis's Central Institution is scheduled to meet on Monday and Thursday, with the institution planning to release its latest policy decision on Thursday at 1:30 p.m. PDT, followed by a press conference where Central Institution Chair Martin Smith will take questions. Investors expect the Market Strategy Committee to hold its benchmark interest rate steady in a range of 3.5%-3.75%.
output triples:
[(MARTIN SMITH, CHAIR OF, CENTRAL INSTITUTION)]
######################
Example 2:
entities: [FIRUZABAD, AURELIA, QUINTARA, TIRUZIA, KROHAARA, CASHION, SAMUEL NAMARA, ALHAMIA PRISON, DURKE BATAGLANI, MEGGIE TAZBAH]
text:
Five Aurelians jailed for 8 years in Firuzabad and widely regarded as hostages are on their way home to Aurelia.

The swap orchestrated by Quintara was finalized when $8bn of Firuzi funds were transferred to financial institutions in Krohaara, the capital of Quintara.

The exchange initiated in Firuzabad's capital, Tiruzia, led to the four men and one woman, who are also Firuzi nationals, boarding a chartered flight to Krohaara.

They were welcomed by senior Aurelian officials and are now on their way to Aurelia's capital, Cashion.

The Aurelians include 39-year-old businessman Samuel Namara, who has been held in Tiruzia's Alhamia Prison, as well as journalist Durke Bataglani, 59, and environmentalist Meggie Tazbah, 53, who also holds Bratinas nationality.

output triples:
[(FIRUZABAD, NEGOTIATED WITH, AURELIA), (QUINTARA, BROKERED EXCHANGE, AURELIA), (QUINTARA, BROKERED EXCHANGE, FIRUZABAD), (SAMUEL NAMARA, DETAINED AT, ALHAMIA PRISON), (SAMUEL NAMARA, EXCHANGED TOGETHER WITH, MEGGIE TAZBAH), (SAMUEL NAMARA, EXCHANGED TOGETHER WITH, DURKE BATAGLANI), (MEGGIE TAZBAH, EXCHANGED TOGETHER WITH, DURKE BATAGLANI), (SAMUEL NAMARA, HOSTAGE IN, FIRUZABAD), (MEGGIE TAZBAH, HOSTAGE IN, FIRUZABAD), (DURKE BATAGLANI, HOSTAGE IN, FIRUZABAD)]
"""


EXAMPLES_FOR_TYPE_ASSERTION="""
Example 1:
entities: [CENTRAL INSTITUTION, MARTIN SMITH, MARKET STRATEGY COMMITTEE]
entity_types: [ORGANIZATION, PERSON]
Text:
The Verdantis's Central Institution is scheduled to meet on Monday and Thursday, with the institution planning to release its latest policy decision on Thursday at 1:30 p.m. PDT, followed by a press conference where Central Institution Chair Martin Smith will take questions. Investors expect the Market Strategy Committee to hold its benchmark interest rate steady in a range of 3.5%-3.75%.
output triples:
[(CENTRAL INSTITUTION, ORGANIZATION), (MARTIN SMITH, PERSON), (MARKET STRATEGY COMMITTEE, ORGANIZATION)]
######################

Example 2:
entities: [FIRUZABAD, AURELIA, QUINTARA, TIRUZIA, KROHAARA, CASHION, SAMUEL NAMARA, ALHAMIA PRISON, DURKE BATAGLANI, MEGGIE TAZBAH]
entity_types: [ORGANIZATION, GEO, PERSON]
text:
Five Aurelians jailed for 8 years in Firuzabad and widely regarded as hostages are on their way home to Aurelia.

The swap orchestrated by Quintara was finalized when $8bn of Firuzi funds were transferred to financial institutions in Krohaara, the capital of Quintara.

The exchange initiated in Firuzabad's capital, Tiruzia, led to the four men and one woman, who are also Firuzi nationals, boarding a chartered flight to Krohaara.

They were welcomed by senior Aurelian officials and are now on their way to Aurelia's capital, Cashion.

The Aurelians include 39-year-old businessman Samuel Namara, who has been held in Tiruzia's Alhamia Prison, as well as journalist Durke Bataglani, 59, and environmentalist Meggie Tazbah, 53, who also holds Bratinas nationality.

output triples:
[(FIRUZABAD, GEO), (AURELIA, GEO), (QUINTARA, GEO), (TIRUZIA, GEO), (KROHAARA, GEO), (CASHION, GEO), (SAMUEL NAMARA, PERSON), (ALHAMIA PRISON, GEO), (DURKE BATAGLANI, PERSON), (MEGGIE TAZBAH, PERSON), ]
"""

EXAMPLES_FOR_TYPE_GENERATION="""
Example 1:
entities: [CENTRAL INSTITUTION, MARTIN SMITH, MARKET STRATEGY COMMITTEE]
Text:
The Verdantis's Central Institution is scheduled to meet on Monday and Thursday, with the institution planning to release its latest policy decision on Thursday at 1:30 p.m. PDT, followed by a press conference where Central Institution Chair Martin Smith will take questions. Investors expect the Market Strategy Committee to hold its benchmark interest rate steady in a range of 3.5%-3.75%.
output triples:
[(CENTRAL INSTITUTION, ORGANIZATION), (MARTIN SMITH, PERSON), (MARKET STRATEGY COMMITTEE, ORGANIZATION)]
######################

Example 2:
entities: [FIRUZABAD, AURELIA, QUINTARA, TIRUZIA, KROHAARA, CASHION, SAMUEL NAMARA, ALHAMIA PRISON, DURKE BATAGLANI, MEGGIE TAZBAH]
text:
Five Aurelians jailed for 8 years in Firuzabad and widely regarded as hostages are on their way home to Aurelia.

The swap orchestrated by Quintara was finalized when $8bn of Firuzi funds were transferred to financial institutions in Krohaara, the capital of Quintara.

The exchange initiated in Firuzabad's capital, Tiruzia, led to the four men and one woman, who are also Firuzi nationals, boarding a chartered flight to Krohaara.

They were welcomed by senior Aurelian officials and are now on their way to Aurelia's capital, Cashion.

The Aurelians include 39-year-old businessman Samuel Namara, who has been held in Tiruzia's Alhamia Prison, as well as journalist Durke Bataglani, 59, and environmentalist Meggie Tazbah, 53, who also holds Bratinas nationality.

output triples:
[(FIRUZABAD, GEO), (AURELIA, GEO), (QUINTARA, GEO), (TIRUZIA, GEO), (KROHAARA, GEO), (CASHION, GEO), (SAMUEL NAMARA, PERSON), (ALHAMIA PRISON, GEO), (DURKE BATAGLANI, PERSON), (MEGGIE TAZBAH, PERSON), ]
"""