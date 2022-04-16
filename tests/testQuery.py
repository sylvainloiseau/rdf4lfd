import rdflib
g.parse("../tests/corpus.ttl")
knows_query = """
SELECT ?title
WHERE {
    ?a a ns1:Event .
    ?a ns1:Title ?title .
}"""
qres = g.query(knows_query)
for row in qres:
     print(f"{row.title}")


knows_query = """ SELECT ?session WHERE {
?session ns1:EventType "DataSession" .
ns1:Recording ?record .
?a ns1:Speaker ?speaker .  }"""
qres = g.query(knows_query)
for row in qres:
     print(f"{row.speaker}")


# to panda : https://github.com/lawlesst/sparql-dataframe
