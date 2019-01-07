import re
from nltk.tokenize import word_tokenize
import SPARQLWrapper
from SPARQLWrapper import SPARQLWrapper, JSON
from collections import OrderedDict
import pandas
from langdetect import detect


def tokenize_topics(topics):
    topics = re.sub("([0-9]*\.[0-9]*)\*", "", topics)
    topics = re.sub('[0-9]\, u|\"|\'|\+|\,|\\[|\\(|\\]|\\)', "", topics)
    tokens_list = word_tokenize(topics)
    return list(set(tokens_list))


def query_wikidata_service(searchterm, language_code):
    query = """SELECT ?item ?itemLabel ?subclass_of ?subclass_ofLabel ?category_of ?category_ofLabel 
        ?instance_of ?instance_ofLabel WHERE { SERVICE wikibase:mwapi { bd:serviceParam wikibase:api "EntitySearch" . 
        bd:serviceParam wikibase:endpoint "www.wikidata.org" . bd:serviceParam mwapi:search '""" + searchterm + """' . 
        bd:serviceParam mwapi:language '""" + language_code + """' . bd:serviceParam wikibase:limit 1 . 
        ?item wikibase:apiOutputItem mwapi:item .} SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } 
        OPTIONAL { ?item (wdt:P279) ?subclass_of.} OPTIONAL { ?item (wdt:P910) ?category_of.} 
        OPTIONAL { ?item (wdt:P31) ?instance_of.}}"""
    url = 'https://query.wikidata.org/sparql'
    sparql = SPARQLWrapper(url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def add_and_link_ontology_nodes(df, skill):
    cypher_list = []
    keys = df.keys()
    for key in keys:
        switch_case = lookup_dict.get(key)
        for b in range(len(df)):
            cypher_list.append("""MERGE (s:Skill {name: '""" + skill + """'}) ON MATCH SET 
                    s.wikidata_url = '""" + str(df['item.value'][b]) + """' RETURN s""")
            if switch_case == 1:
                cypher_list.append("""MERGE (o:Ontology_Item {wikidata_url: '""" + str(df['subclass_of.value'][b]) + """', 
                    name: '""" + str(df['subclass_ofLabel.value'][b]) + """'})""")
                cypher_list.append("""MATCH (s:Skill), (o:Ontology_Item) WHERE s.wikidata_url = '""" + str(df['item.value'][b]) + """' AND
                 o.wikidata_url = '""" + str(df['subclass_of.value'][b]) + """' MERGE (s)-[rel:SUBCLASS_OF]->(o)""")
            if switch_case == 2:
                cypher_list.append("""MERGE (o:Ontology_Item {wikidata_url: '""" + str(df['category_of.value'][b]) + """', 
                    name: '""" + str(df['category_ofLabel.value'][b]) + """'})""")
                cypher_list.append("""MATCH (s:Skill), (o:Ontology_Item) WHERE s.wikidata_url = '""" + str(df['item.value'][b]) + """' AND
                    o.wikidata_url = '""" + str(df['category_of.value'][b]) + """' MERGE (s)-[rel:CATEGORY_OF]->(o)""")
            if switch_case == 3:
                cypher_list.append("""MERGE (o:Ontology_Item {wikidata_url: '""" + str(df['instance_of.value'][b]) + """', 
                    name: '""" + str(df['instance_ofLabel.value'][b]) + """'})""")
                cypher_list.append("""MATCH (s:Skill), (o:Ontology_Item) WHERE s.wikidata_url = '""" + str(df['item.value'][b]) + """' AND
                    o.wikidata_url = '""" + str(df['instance_of.value'][b]) + """' MERGE (s)-[rel:INSTANCE_OF]->(o)""")
    return OrderedDict((x, True) for x in cypher_list).keys()


graph = Graph("http://127.0.0.1:7474", auth=("neo4j", "root"))

# lookup-list to be used in combination with add_ontology_nodes_to_graph
lookup_dict = {
        "item.value": 1,
        "itemLabel.value": 1,
        "subclass_of.value": 2,
        "subclass_ofLabel.value": 2,
        "category_of.value": 3,
        "category_ofLabel.value": 3,
        "instance_of.value": 4,
        "instance_ofLabel.value": 4
        }

# instead of computing-intense pandas operations, directly create the nodes and relationships
for i in range(len(slides_df)):
    tokens_list = tokenize_topics(slides_df.iloc[i,5])
    # detect language to annotate in SPARQL query, because [AUTO_LANGUAGE] has performance issues
    language_code = detect(str(tokens_list))
    for token in tokens_list:
        try:
            service_resp_list = query_wikidata_service(token, language_code)
            df = pandas.io.json.json_normalize(service_resp_list['results']['bindings'])
            cypher_list = ["""MERGE (s:Skill {name: '""" + token + """'})""", """MATCH (p:Consulting_Profile), (s:Skill) WHERE 
            p.uuid = '""" + str(i) + """' AND s.name = '""" + token + """' MERGE (p)-[rel:HAS_SKILL]->(s)"""]
            for stmnt in cypher_list:
                graph.run(stmnt)
            if len(df) > 0:
                onto_items_list = add_and_link_ontology_nodes(df, token)
                for onto_item in onto_items_list:
                    graph.run(onto_item)
        except:
            pass