SCHEMA_QUERIES = [
    "CREATE INDEX IF NOT EXISTS FOR (n:User) ON (n.id)",
    "CREATE INDEX IF NOT EXISTS FOR (n:Topic) ON (n.id)",
    "CREATE INDEX IF NOT EXISTS FOR (n:Resource) ON (n.id)",
    "CREATE INDEX IF NOT EXISTS FOR (n:Progress) ON (n.id)",
]

SEED_QUERY = """
CREATE (u:User {id:'u_001', name:'Aisha Khan', available_minutes:45}),
       (python:Topic {id:'t_python', name:'Python Functions', difficulty:2, estimated_minutes:35, description:'Reusable functions, arguments, and return values'}),
    (data:Topic {id:'t_data', name:'Data Structures', difficulty:3, estimated_minutes:45, description:'Lists, dictionaries, sets, and tuples'}),
       (recursion:Topic {id:'t_recursion', name:'Recursion', difficulty:4, estimated_minutes:45, description:'Solving problems with self-referential functions'}),
       (testing:Topic {id:'t_testing', name:'Python Testing', difficulty:3, estimated_minutes:30, description:'Reliable tests with pytest'}),
       (r1:Resource {id:'r_functions', title:'Functions in Practice', kind:'article', minutes:20, url:'https://docs.python.org/3/tutorial/controlflow.html#defining-functions'}),
       (r2:Resource {id:'r_data', title:'Choosing the Right Collection', kind:'video', minutes:30, url:'https://docs.python.org/3/tutorial/datastructures.html'}),
       (r3:Resource {id:'r_testing', title:'Testing a Small Python Project', kind:'lab', minutes:25, url:'https://docs.pytest.org/en/stable/getting-started.html'}),
       (q1:Quiz {id:'q_functions', title:'Functions Checkpoint', minutes:10}),
       (q2:Quiz {id:'q_data', title:'Data Structures Checkpoint', minutes:10}),
       (p1:Progress {id:'p_python', mastery:0.82, status:'mastered'}),
       (p2:Progress {id:'p_data', mastery:0.42, status:'in_progress'}),
       (gap:SkillGap {id:'gap_data', severity:0.58, reason:'Recent quiz score below 60%'}),
       (u)-[:HAS_PROGRESS]->(p1)-[:FOR_TOPIC]->(python),
       (u)-[:HAS_PROGRESS]->(p2)-[:FOR_TOPIC]->(data),
       (u)-[:HAS_GAP]->(gap)-[:FOR_TOPIC]->(data),
       (python)-[:PREREQUISITE_OF]->(data),
       (data)-[:PREREQUISITE_OF]->(recursion),
       (data)-[:PREREQUISITE_OF]->(testing),
       (python)-[:HAS_RESOURCE]->(r1),
       (data)-[:HAS_RESOURCE]->(r2),
       (testing)-[:HAS_RESOURCE]->(r3),
       (python)-[:HAS_QUIZ]->(q1),
       (data)-[:HAS_QUIZ]->(q2)
"""
