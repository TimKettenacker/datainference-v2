import re
import py2neo
from py2neo import Graph


def extract_node_definitions(tuples_list):
    nodes_list = []
    for tuple in tuples_list:
        try:
            nodes_list.append((re.sub("[^\w]", " ", str(max(tuple)).title())).strip())
        except:
            pass
    return list(set(nodes_list))


graph = Graph("http://127.0.0.1:7474", auth=("neo4j", "root"))

# first, create all consultants, roles and industries INDEPENDENT(!) from each other;
# this prevents duplicates from being created when relationships are being created later on
for a in range(len(slides_df)):
    name = "Consulting Profile no." + str(a)
    cypher1 = "MERGE (p:Consulting_Profile {uuid: '" + str(a) + "', name: '" + name + "'})"
    graph.run(cypher1)

role_nodes_list = extract_node_definitions([item for sublist in slides_df["raw roles"] for item in sublist])
industry_nodes_list = extract_node_definitions([item for sublist in slides_df["raw industries"] for item in sublist])

for role in role_nodes_list:
    cypher2 = "MERGE (r:Role {name: '" + role + "'})"
    graph.run(cypher2)

for industry in industry_nodes_list:
    cypher3 = "MERGE (i:Industry {name: '" + industry + "'})"
    graph.run(cypher3)

# establish corresponding relationship between profiles & roles
for a in range(len(slides_df)):
    roles = extract_node_definitions(slides_df.at[a, "raw roles"])
    for role in roles:
        cypher4 = """MATCH (p:Consulting_Profile), (r:Role)  WHERE p.uuid = '""" + str(a) + """' AND 
        r.name = '""" + role + """' MERGE (p)-[rel:HAS_TAKEN_ROLE]->(r) RETURN rel"""
        graph.run(cypher4)

# establish corresponding relationship between profiles & industries
for a in range(len(slides_df)):
    industries = extract_node_definitions(slides_df.at[a, "raw industries"])
    for industry in industries:
        cypher5 = """MATCH (p:Consulting_Profile), (i:Industry)  WHERE p.uuid = '""" + str(a) + """' AND 
        i.name = '""" + industry + """' MERGE (p)-[rel:HAS_INDUSTRY_EXPERIENCE]->(i) RETURN rel"""
        graph.run(cypher5)