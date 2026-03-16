_verdantis_institution = "The Verdantis's Central Institution is scheduled to meet on Monday and Thursday, with the institution planning to release its latest policy decision on Thursday at 1:30 p.m. PDT, followed by a press conference where Central Institution Chair Martin Smith will take questions. Investors expect the Market Strategy Committee to hold its benchmark interest rate steady in a range of 3.5%-3.75%."
_verdantis_entities = "[CENTRAL INSTITUTION, MARTIN SMITH, MARKET STRATEGY COMMITTEE]"
_jailed_aurelians = """Five Aurelians jailed for 8 years in Firuzabad and widely regarded as hostages are on their way home to Aurelia.

The swap orchestrated by Quintara was finalized when $8bn of Firuzi funds were transferred to financial institutions in Krohaara, the capital of Quintara.

The exchange initiated in Firuzabad's capital, Tiruzia, led to the four men and one woman, who are also Firuzi nationals, boarding a chartered flight to Krohaara.

They were welcomed by senior Aurelian officials and are now on their way to Aurelia's capital, Cashion.

The Aurelians include 39-year-old businessman Samuel Namara, who has been held in Tiruzia's Alhamia Prison, as well as journalist Durke Bataglani, 59, and environmentalist Meggie Tazbah, 53, who also holds Bratinas nationality.
"""
_jailed_aurelians_entities = "[FIRUZABAD, AURELIA, QUINTARA, TIRUZIA, KROHAARA, CASHION, SAMUEL NAMARA, ALHAMIA PRISON, DURKE BATAGLANI, MEGGIE TAZBAH]"

EXAMPLES_FOR_ENTITY_EXTRACTION = f"""
Example 1:
text:
{_verdantis_institution}
output entities:
{_verdantis_entities}

######################
Example 2:
text:
{_jailed_aurelians}

output entities:
{_jailed_aurelians_entities}
"""

EXAMPLES_FOR_TRIPLES_EXTRACTION = f"""
Example 1:
entities: {_verdantis_entities}
text:
{_verdantis_institution}
output triples:
[(MARTIN SMITH, CHAIR OF, CENTRAL INSTITUTION)]
######################
Example 2:
entities: {_jailed_aurelians_entities}
text:
{_jailed_aurelians}
output triples:
[(FIRUZABAD, NEGOTIATED WITH, AURELIA), (QUINTARA, BROKERED EXCHANGE, AURELIA), (QUINTARA, BROKERED EXCHANGE, FIRUZABAD), (SAMUEL NAMARA, DETAINED AT, ALHAMIA PRISON), (SAMUEL NAMARA, EXCHANGED TOGETHER WITH, MEGGIE TAZBAH), (SAMUEL NAMARA, EXCHANGED TOGETHER WITH, DURKE BATAGLANI), (MEGGIE TAZBAH, EXCHANGED TOGETHER WITH, DURKE BATAGLANI), (SAMUEL NAMARA, HOSTAGE IN, FIRUZABAD), (MEGGIE TAZBAH, HOSTAGE IN, FIRUZABAD), (DURKE BATAGLANI, HOSTAGE IN, FIRUZABAD)]
"""


EXAMPLES_FOR_TYPE_ASSERTION= f"""
Example 1:
entities: {_verdantis_entities}
entity_types: [ORGANIZATION, PERSON]
text:
{_verdantis_institution}
output pairs:
[(CENTRAL INSTITUTION, ORGANIZATION), (MARTIN SMITH, PERSON), (MARKET STRATEGY COMMITTEE, ORGANIZATION)]
######################

Example 2:
entities: {_jailed_aurelians_entities}
entity_types: [ORGANIZATION, GEO, PERSON]
text:
{_jailed_aurelians}
output pairs:
[(FIRUZABAD, GEO), (AURELIA, GEO), (QUINTARA, GEO), (TIRUZIA, GEO), (KROHAARA, GEO), (CASHION, GEO), (SAMUEL NAMARA, PERSON), (ALHAMIA PRISON, GEO), (DURKE BATAGLANI, PERSON), (MEGGIE TAZBAH, PERSON)]
"""

EXAMPLES_FOR_TYPE_GENERATION=f"""
Example 1:
entities: {_verdantis_entities}
text:
{_verdantis_institution}
output pairs:
[(CENTRAL INSTITUTION, ORGANIZATION), (MARTIN SMITH, PERSON), (MARKET STRATEGY COMMITTEE, ORGANIZATION)]
######################

Example 2:
entities: {_jailed_aurelians_entities}
text:
{_jailed_aurelians}
output pairs:
[(FIRUZABAD, GEO), (AURELIA, GEO), (QUINTARA, GEO), (TIRUZIA, GEO), (KROHAARA, GEO), (CASHION, GEO), (SAMUEL NAMARA, PERSON), (ALHAMIA PRISON, GEO), (DURKE BATAGLANI, PERSON), (MEGGIE TAZBAH, PERSON)]
"""


EXAMPLES_FOR_LITERAL_EXTRACTION = f"""
Example 1:
entities: {_verdantis_entities}
text:
{_verdantis_institution}
output triples:
[THURSDAY AT 1:30 P.M. PDT, 3.5%-3.75%]
######################

Example 2:
entities: {_jailed_aurelians_entities}
text:
{_jailed_aurelians}
output triples:
[39, 59, 53]
"""

EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION= f"""
Example 1:
entities: {_verdantis_entities}
numeric_literals: [THURSDAY AT 1:30 P.M. PDT, 3.5%-3.75%]
text:
{_verdantis_institution}
output triples:
[(CENTRAL INSTITUTION, RELEASE DECISION, THURSDAY AT 1:30 P.M. PDT), (MARKET STRATEGY COMMITTEE, EXPECTED INTEREST RATE, 3.5%-3.75%)]
######################

Example 2:
entities: {_jailed_aurelians_entities}
numeric_literals: [39, 59, 53]
text:
{_jailed_aurelians}
output triples:
[(SAMUEL NAMARA, HAS AGE, 39), (DURKE BATAGLANI, HAS AGE, 59), (MEGGIE TAZBAH, HAS AGE, 53)]
"""