from rdflib import Graph

class TestQuery():

    @staticmethod
    def test_query():
          g = Graph()
          g.parse("rdf4lfd/sample/data/rdf/from_spreadsheet_ods/Index.ttl")
          knows_query = """
          SELECT ?title
          WHERE {
          ?a a ns1:Event .
          ?a ns1:Title ?title .
          }"""
          qres = g.query(knows_query)
          for row in qres:
               pass
               #print(f"{row.title}")


          knows_query = """
          SELECT ?speaker
          WHERE {
          ?a ns1:EventType "DataSession" .
          ?a ns1:Recording ?record .
          ?a ns1:Speaker ?speaker .
          }"""
          qres = g.query(knows_query)
          for row in qres:
               print(f"{row.speaker}")


     # to panda : https://github.com/lawlesst/sparql-dataframe
