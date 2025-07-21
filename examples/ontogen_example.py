import time

from owlapy.ontogen.data_extraction import GraphExtractor
from owlapy.owl_ontology import SyncOntology

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

text_example_4 = """In this video, we sit down with Sean O’Dowd, a former consultant at BCG who transitioned into 
entrepreneurship as the CEO of Scholastic Capital. Sean shares his journey from advising companies to building his 
own business, leveraging his expertise in real estate acquisitions. He dives into the challenges and opportunities of 
leaving a corporate career to pursue his vision. Along the way, Sean offers invaluable wisdom, practical insights, and 
actionable tips for aspiring entrepreneurs. Whether you’re considering starting your own venture or curious about the 
mindset shift from consultant to CEO, this conversation is packed with inspiration and advice.
"""

text_example_5 = """Concetta Franconero was born on Dec. 12, 1937, in Newark and grew up in the Ironbound neighborhood. Her father, the son of Italian immigrants, was a dockworker and a roofer who loved to play the concertina, and he put an accordion in his daughter’s hands when she was 3.

From that moment, he hovered over her musical development and her career, putting her onstage at local lodges and churches. She made her stage debut at 4, singing “Anchors Aweigh” and accompanying herself on the accordion at Olympic Park in Irvington, N.J.

At 11, she was a regular on “Marie Moser’s Starlets,” a local television variety show. After she appeared on Ted Mack’s “Original Amateur Hour” and “Arthur Godfrey’s Talent Scouts,” Mr. Mack advised her to lose the accordion, and Mr. Godfrey advised her to change her last name to Francis. She then embarked on a four-year run as one of the child entertainers on the anthology series “Startime.”

As she outgrew the child-star category, Ms. Francis obtained forged documents and began singing in clubs and lounges. Imitating the vocal styles of stars like Patti Page and Rosemary Clooney, she made demonstration tapes for music publishers who wanted to place their songs with famous singers.

In 1955 she signed a contract with MGM Records, and over the next two years she recorded 10 singles, all of them flops. “The bombs just kept a-comin’,” she wrote in “Who’s Sorry Now?,” her 1984 memoir. “They were becoming my trademark, a foregone conclusion.”

Down to her last record and ready to quit show business to attend college, she gave in to her father’s wishes and recorded “Who’s Sorry Now,” a song she loathed because she thought it sounded old-fashioned. It was first heard on Dick Clark’s “American Bandstand” on Jan. 1, 1958, and sold a million copies in the next six months.

“It was the first time I ever recorded that I didn’t try to imitate somebody else,” Ms. Francis told Gary James in an interview for classicbands.com in 1994. “I hated the song so much that I didn’t care what I sounded like. So I just sang it.”

For the next four years, Ms. Francis reigned as queen of the charts, not only in the United States but around the world. She sang in foreign languages when required — her first such hit was “Mama” in 1960, recorded after she learned Italian — and released albums including “Connie Francis Sings Italian Favorites,” “Connie Francis Sings Jewish favorites” and “Connie Francis Sings Irish Favorites.”

Always intent on broadening her appeal, Ms. Francis made a practice of recording her songs in several languages, beginning with “Everybody’s Somebody’s Fool,” which became Europe’s top single in 1960.

In 1960, Ms. Francis took a leading role in the teen-vacation melodrama “Where the Boys Are” and performed its plaintive theme song, which became a Top 10 hit. (She had already made her film debut in 1956 dubbing Tuesday Weld’s voice in “Rock, Rock, Rock!,” an early jukebox musical.) Although she later said she hated her performance in “Where the Boys Are,” she appeared in three sequels, “Follow the Boys” (1963), “Looking for Love” (1964) and “When the Boys Meet the Girls” (1965).

Like the singer and songwriter Bobby Darin, with whom she was romantically involved until her father chased him off with a gun, Ms. Francis reached out beyond her teenage audience, recording material that made her a natural in Las Vegas as well as in nightclubs like the Copacabana in New York. She was also a sought-after entertainer on television variety shows.

She briefly tried performing before teenage audiences, but she found that she did not care for the experience.

“I always remember receiving much more applause from teenagers when I was introduced than at any other time during the show — especially after my closing number,” she wrote in her memoir. “After my name was announced and the squeals of delight subsided, it was downhill all the way.”

With the ascendancy of the Beatles, Ms. Francis’s days on the pop charts were over; her last Top 40 hit was “Be Anything (But Be Mine”) in 1964. But she retained an enormous following among older audiences, especially overseas, where fans routinely voted her their favorite female vocalist.

In 1974, after performing at the Westbury Music Fair on Long Island, she was raped at knifepoint and then robbed in her nearby motel. She later sued the motel and was awarded $2.5 million in damages, at the time one of the largest awards ever made in a rape case.

The experience threw Ms. Francis into an emotional tailspin, and she descended into a nightmare of paranoia, suicidal depression and drug abuse. Eventually, after being committed to a mental hospital by her father in the early 1980s, she was found to be suffering from manic depression. (She later said that she had been misdiagnosed, and that what she actually had was post-traumatic stress disorder “following a horrendous string of events in my life.”)

She suffered other setbacks over the years. In 1967, cosmetic surgery on her nose left her unable to sing in an air-conditioned room, making it impossible to perform in most clubs and Las Vegas casinos. Corrective surgery a decade later caused her to lose her voice entirely. In 1981, her younger brother, George, was murdered.

Not long after her voice failed, her fourth husband, the television producer Bob Parkinson, left her. Three previous marriages, to Dick Kanellis, Izadore Marion and Joseph Garzilli, had ended in divorce.

Information on her survivors was not immediately available.

In 1981, after additional surgery, she recovered her voice. Ms. Francis returned to the Westbury Music Fair and performed a comeback concert.

“I often say, I’d like to be remembered not for the highs I’ve reached but for the depths from which I’ve risen,” she told Mr. James. “There were exhilarating highs and abysmal lows. But it was fighting to get out of those lows that I feel most proud of.
"""

start = time.time()
ontogen = GraphExtractor(model="Qwen/Qwen3-32B-AWQ",api_key="<ENTER_YOUR_KEY>", api_base=None,
                         temperature=0.1, seed=42, enable_logging=True)
ontogen.forward(text=text_example_3, generate_types = True, extract_spl_triples=True)
print(f"Runtime: {time.time() - start}")

onto = SyncOntology(path="generated_ontology.owl")

[print(ax) for ax in onto.get_abox_axioms()]
[print(ax) for ax in onto.get_tbox_axioms()]


# ================= Results using model=Qwen/Qwen3-32B-AWQ, temperature=0.1, seed=42 =================
# For text example no.1 (runtime ~ 62s)
# GraphExtractor: INFO  :: Generated the following entities: ['NEOCHIP', 'NEWTECH EXCHANGE', 'QUANTUM SYSTEMS', 'IoT']
# GraphExtractor: INFO  :: Generated the following triples: [('NEOCHIP', 'TRADING ON', 'NEWTECH EXCHANGE'), ('NEOCHIP', 'ACQUIRED BY', 'QUANTUM SYSTEMS'), ('NEOCHIP', 'SPECIALIZES IN', 'IOT')]
# GraphExtractor: INFO  :: Finished generating types and assigned them to entities as following: [('NEOCHIP', 'ORGANIZATION'), ('NEWTECH EXCHANGE', 'ORGANIZATION'), ('QUANTUM SYSTEMS', 'ORGANIZATION'), ('IoT', 'CONCEPT')]
# GraphExtractor: INFO  :: Generated the following numeric literals: ['2016']
# GraphExtractor: INFO  :: Generated the following s-p-l triples: []

#######################
# For text example no.2 (runtime ~ 72s)
# GraphExtractor: INFO  :: Generated the following entities: ['TRUMP', 'NATO', 'OVAL OFFICE', 'BBC', 'BUTLER', 'PENNSYLVANIA']
# GraphExtractor: INFO  :: Generated the following triples: [('TRUMP', 'ENDORSED', 'NATO'), ('TRUMP', 'MADE PHONE CALL TO', 'BBC'), ('TRUMP', 'INTERVIEWED FROM', 'OVAL OFFICE'), ('BUTLER', 'LOCATED IN', 'PENNSYLVANIA')]
# GraphExtractor: INFO  :: Finished generating types and assigned them to entities as following: [('TRUMP', 'PERSON'), ('NATO', 'ORGANIZATION'), ('OVAL OFFICE', 'GEO'), ('BBC', 'ORGANIZATION'), ('BUTLER', 'GEO'), ('PENNSYLVANIA', 'GEO')]
# GraphExtractor: INFO  :: Generated the following numeric literals: ['20', '1']
# GraphExtractor: INFO  :: Generated the following s-p-l triples: []

#######################
# For text example no.3 (runtime ~ 44s)
# GraphExtractor: INFO  :: Generated the following entities: ['J.P. MORGAN & CO.', 'JPMORGAN CHASE', 'J. P. MORGAN', 'HOUSE OF MORGAN', 'MORGAN']
# GraphExtractor: INFO  :: Generated the following triples: [('J. P. MORGAN', 'FOUNDED', 'J.P. MORGAN & CO.'), ('J.P. MORGAN & CO.', 'SUBSIDIARY OF', 'JPMORGAN CHASE'), ('J.P. MORGAN & CO.', 'ALTERNATIVELY KNOWN AS', 'HOUSE OF MORGAN'), ('J.P. MORGAN & CO.', 'ALTERNATIVELY KNOWN AS', 'MORGAN')]
# GraphExtractor: INFO  :: Finished generating types and assigned them to entities as following: [('J.P. MORGAN & CO.', 'ORGANIZATION'), ('JPMORGAN CHASE', 'ORGANIZATION'), ('J. P. MORGAN', 'PERSON'), ('HOUSE OF MORGAN', 'ORGANIZATION'), ('MORGAN', 'ORGANIZATION')]
# GraphExtractor: INFO  :: Generated the following numeric literals: ['1871']
# GraphExtractor: INFO  :: Generated the following s-p-l triples: [('J.P. MORGAN & CO.', 'FOUNDED IN', '1871')]

#######################
# For text example no.4 (runtime ~ 36s)
# GraphExtractor: INFO  :: Generated the following entities: ['SEAN O’DOWD', 'BCG', 'SCHOLASTIC CAPITAL']
# GraphExtractor: INFO  :: Generated the following triples: [("SEAN O'DOWD", 'FORMER CONSULTANT AT', 'BCG'), ("SEAN O'DOWD", 'CEO OF', 'SCHOLASTIC CAPITAL')]
# GraphExtractor: INFO  :: Finished generating types and assigned them to entities as following: [('SEAN O’DOWD', 'PERSON'), ('BCG', 'ORGANIZATION'), ('SCHOLASTIC CAPITAL', 'ORGANIZATION')]
# GraphExtractor: INFO  :: Generated the following numeric literals: []
# GraphExtractor: INFO  :: Generated the following s-p-l triples: []

#######################
# For text example no.5 (runtime ~ 127s)
# GraphExtractor: INFO  :: Generated the following entities: ['CONCETTA FRANCONERO', 'CONNIE FRANCIS', 'IRONBOUND NEIGHBORHOOD', 'NEWARK', 'IRVINGTON, N.J.', 'TED MACK', 'ORIGINAL AMATEUR HOUR', 'ARTHUR GODFREY', 'TALENT SCOUTS', 'STARTIME', 'MGM RECORDS', 'WHO’S SORRY NOW', 'AMERICAN BANDSTAND', 'MAMA', 'EVERYBODY’S SOMEONE’S FOOL', 'WHERE THE BOYS ARE', 'FOLLOW THE BOYS', 'LOOKING FOR LOVE', 'WHEN THE BOYS MEET THE GIRLS', 'COPACABANA', 'BOBBY DARIN', 'THE BEATLES', 'WESTBURY MUSIC FAIR', 'LONG ISLAND', 'GARY JAMES', 'DICK KANELLIS', 'IZADORE MARION', 'JOSEPH GARZILLI', 'BOB PARKINSON', 'GEORGE', 'WHO’S SORRY NOW?']
# GraphExtractor: INFO  :: Generated the following triples: [('CONCETTA FRANCONERO', 'BECAME', 'CONNIE FRANCIS'), ('CONCETTA FRANCONERO', 'BORN IN', 'NEWARK'), ('CONCETTA FRANCONERO', 'Grew up in', 'IRONBOUND NEIGHBORHOOD'), ('CONNIE FRANCIS', 'APPEARED ON', 'TED MACK'), ('CONNIE FRANCIS', 'APPEARED ON', 'ORIGINAL AMATEUR HOUR'), ('CONNIE FRANCIS', 'APPEARED ON', 'ARTHUR GODFREY'), ('CONNIE FRANCIS', 'APPEARED ON', 'TALENT SCOUTS'), ('CONNIE FRANCIS', 'PART OF', 'STARTIME'), ('CONNIE FRANCIS', 'RECORDED', 'WHO’S SORRY NOW'), ('WHO’S SORRY NOW', 'FIRST HEARD ON', 'AMERICAN BANDSTAND'), ('CONNIE FRANCIS', 'RECORDED', 'MAMA'), ('CONNIE FRANCIS', 'RECORDED', 'EVERYBODY’S SOMEONE’S FOOL'), ('CONNIE FRANCIS', 'STARRED IN', 'WHERE THE BOYS ARE'), ('CONNIE FRANCIS', 'STARRED IN', 'FOLLOW THE BOYS'), ('CONNIE FRANCIS', 'STARRED IN', 'LOOKING FOR LOVE'), ('CONNIE FRANCIS', 'STARRED IN', 'WHEN THE BOYS MEET THE GIRLS'), ('CONNIE FRANCIS', 'PERFORMED AT', 'COPACABANA'), ('CONNIE FRANCIS', 'ROMANTIC INVOLVEMENT WITH', 'BOBBY DARIN'), ('CONNIE FRANCIS', 'OUTGROWN BY', 'THE BEATLES'), ('CONNIE FRANCIS', 'PERFORMED AT', 'WESTBURY MUSIC FAIR'), ('CONNIE FRANCIS', 'INTERVIEWED BY', 'GARY JAMES'), ('CONNIE FRANCIS', 'MARRIED TO', 'DICK KANELLIS'), ('CONNIE FRANCIS', 'MARRIED TO', 'IZADORE MARION'), ('CONNIE FRANCIS', 'MARRIED TO', 'JOSEPH GARZILLI'), ('CONNIE FRANCIS', 'MARRIED TO', 'BOB PARKINSON'), ('CONNIE FRANCIS', 'BROTHER', 'GEORGE')]
# GraphExtractor: INFO  :: Finished generating types and assigned them to entities as following: [('CONCETTA FRANCONERO', 'PERSON'), ('CONNIE FRANCIS', 'PERSON'), ('IRONBOUND NEIGHBORHOOD', 'GEO'), ('NEWARK', 'GEO'), ('IRVINGTON, N.J.', 'GEO'), ('TED MACK', 'PERSON'), ('ORIGINAL AMATEUR HOUR', 'WORK'), ('ARTHUR GODFREY', 'PERSON'), ('TALENT SCOUTS', 'WORK'), ('STARTIME', 'WORK'), ('MGM RECORDS', 'ORGANIZATION'), ('WHO’S SORRY NOW', 'WORK'), ('AMERICAN BANDSTAND', 'WORK'), ('MAMA', 'WORK'), ('EVERYBODY’S SOMEONE’S FOOL', 'WORK'), ('WHERE THE BOYS ARE', 'WORK'), ('FOLLOW THE BOYS', 'WORK'), ('LOOKING FOR LOVE', 'WORK'), ('WHEN THE BOYS MEET THE GIRLS', 'WORK'), ('COPACABANA', 'GEO'), ('BOBBY DARIN', 'PERSON'), ('THE BEATLES', 'PERSON'), ('WESTBURY MUSIC FAIR', 'GEO'), ('LONG ISLAND', 'GEO'), ('GARY JAMES', 'PERSON'), ('DICK KANELLIS', 'PERSON'), ('IZADORE MARION', 'PERSON'), ('JOSEPH GARZILLI', 'PERSON'), ('BOB PARKINSON', 'PERSON'), ('GEORGE', 'PERSON'), ('WHO’S SORRY NOW?', 'WORK')]
# GraphExtractor: INFO  :: Generated the following numeric literals: ['1937', '3', '4', '11', '1955', '2', '10', '1958', '6', '1,000,000', '4', '1960', '1963', '1964', '1965', '1964', '1974', '$2.5 million', '1981', '4', '3']
# GraphExtractor: INFO  :: Generated the following s-p-l triples: [('CONCETTA FRANCONERO', 'BORN ON', '1937'), ('CONCETTA FRANCONERO', 'AGE WHEN GAVE ACCORDION', '3'), ('CONCETTA FRANCONERO', 'STAGE DEBUT AGE', '4'), ('CONCETTA FRANCONERO', 'APPEARED ON LOCAL TV SHOW AT AGE', '11'), ('MGM RECORDS', 'YEAR SIGNED', '1955'), ('MGM RECORDS', 'NUMBER OF SINGLES RECORDED', '10'), ('WHO’S SORRY NOW', 'RELEASED ON', '1958'), ('WHO’S SORRY NOW', 'COPIES SOLD IN 6 MONTHS', '1,000,000'), ('EVERYBODY’S SOMEONE’S FOOL', 'YEAR BECAME EUROPE’S TOP SINGLE', '1960'), ('WHERE THE BOYS ARE', 'RELEASED IN', '1960'), ('FOLLOW THE BOYS', 'RELEASED IN', '1963'), ('LOOKING FOR LOVE', 'RELEASED IN', '1964'), ('WHEN THE BOYS MEET THE GIRLS', 'RELEASED IN', '1965'), ('MGM RECORDS', 'LAST TOP 40 HIT YEAR', '1964'), ('MOTEL LAWSUIT DAMAGES AWARDED', 'AMOUNT', '$2.5 million'), ('MOTEL LAWSUIT DAMAGES AWARDED', 'YEAR', '1974'), ('VOICE RECOVERY', 'YEAR', '1981')]