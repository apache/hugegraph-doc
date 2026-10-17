/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements. See the NOTICE file distributed with this
 * work for additional information regarding copyright ownership. The ASF
 * licenses this file to You under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import org.apache.hugegraph.driver.HugeClient;
import org.apache.hugegraph.driver.SchemaManager;
import org.apache.hugegraph.structure.constant.T;
import org.apache.hugegraph.structure.graph.Edge;
import org.apache.hugegraph.structure.graph.Vertex;

public class ReleaseClientSmoke {
    public static void main(String[] args) throws Exception {
        try (HugeClient client = HugeClient.builder("http://127.0.0.1:8080", "DEFAULT", "hugegraph")
                                           .configUser("admin", "release-smoke").build()) {
            SchemaManager schema = client.schema();
            schema.propertyKey("release_name").asText().create();
            schema.vertexLabel("release_person").properties("release_name")
                  .primaryKeys("release_name").create();
            schema.edgeLabel("release_knows").sourceLabel("release_person")
                  .targetLabel("release_person").create();
            Vertex first = client.graph().addVertex(T.LABEL, "release_person", "release_name", "first");
            Vertex second = client.graph().addVertex(T.LABEL, "release_person", "release_name", "second");
            Edge edge = first.addEdge("release_knows", second);
            long vertices = client.gremlin().gremlin("g.V().hasLabel('release_person').count()")
                                  .execute().get(0).getLong();
            long edges = client.gremlin().gremlin("g.E().hasLabel('release_knows').count()")
                               .execute().get(0).getLong();
            if (vertices != 2 || edges != 1) {
                throw new IllegalStateException("Client write/query mismatch: " + vertices + "/" + edges);
            }
            client.graph().removeEdge(edge.id());
            client.graph().removeVertex(first.id());
            client.graph().removeVertex(second.id());
            if (client.gremlin().gremlin("g.V().hasLabel('release_person').count()")
                      .execute().get(0).getLong() != 0) {
                throw new IllegalStateException("Client cleanup failed");
            }
            schema.edgeLabel("release_knows").remove();
            schema.vertexLabel("release_person").remove();
            schema.propertyKey("release_name").remove();
            System.out.println("PASS: Client schema, vertices, edge, queries and cleanup");
        }
    }
}
