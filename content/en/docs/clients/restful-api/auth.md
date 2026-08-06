---
title: "Authentication API"
linkTitle: "Authentication"
weight: 16
description: "Authentication REST API: Manage users, roles, permissions, and access control to implement fine-grained graph data security."
---

> **Version Change Notice**:
> - 1.7.0+: Auth API paths use GraphSpace format, such as `/graphspaces/DEFAULT/auth/users`, and group/target IDs match their names (e.g., `admin`)
> - 1.5.x and earlier: Auth API paths include graph name, and group/target IDs use format like `-69:grant`. See [HugeGraph 1.5.x RESTful API](https://github.com/apache/hugegraph-doc/tree/release-1.5.0)

### 10.1 User Authentication and Access Control

> To enable authentication and related configurations, please refer to the [Authentication Configuration](/docs/config/config-authentication/) documentation.

##### Overview of User Authentication and Access Control:
HugeGraph supports multi-user authentication and fine-grained access control. It adopts a 4-tier design based on "User-User Group-Operation-Resource" to flexibly control user roles and permissions. Resources describe data in the graph database, such as vertices that meet certain conditions. Each resource consists of three elements: type, label, and properties. There are a total of 18 types and combinations of any label and properties to form resources. The internal condition of a resource is an "AND" relationship, while the condition between multiple resources is an "OR" relationship. Users can belong to one or more user groups, and each user group can have permissions for any number of resources. The types of operations include read, write, delete, execute, etc. HugeGraph supports dynamically creating users, user groups, and resources, and supports dynamically assigning or revoking permissions. During the initialization of the database, a super administrator user is created, and subsequently, various role users can be created by the super administrator. If a newly created user is assigned sufficient permissions, they can create or manage more users.

##### Example:
user(name=boss) -belong-> group(name=all) -access(read)-> target(graph=graph1, resource={label: person, city: Beijing})  
Description: User 'boss' has read permission for people in the 'graph1' graph from Beijing.

##### Interface Description:
The user authentication and access control interface includes 5 categories: UserAPI, GroupAPI, TargetAPI, BelongAPI, AccessAPI.
**Note** Before 1.5.0, the format of ids such as group/target was similar to -69:grant. After 1.7.0, the id and name were consistent. Such as admin [HugeGraph 1.5 x RESTful API](https://github.com/apache/hugegraph-doc/tree/release-1.5.0)

### 10.2 User (User) API
The user interface includes APIs for creating users, deleting users, modifying users, and querying user-related information.

#### 10.2.1 Create User

##### Params

- user_name: User name
- user_password: User password
- user_phone: User phone number
- user_email: User email

Both user_name and user_password are required.

##### Request Body

```json
{
    "user_name": "boss",
    "user_password": "******",
    "user_phone": "182****9088",
    "user_email": "123@xx.com"
}
```


##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/auth/users
```

##### Response Status

```json
201 
```

##### Response Body
In the response message, the password is encrypted as ciphertext.
```json
{
    "user_password": "******",
    "user_email": "123@xx.com",
    "user_update": "2020-11-17 14:31:07.833",
    "user_name": "boss",
    "user_creator": "admin",
    "user_phone": "182****9088",
    "id": "boss",
    "user_create": "2020-11-17 14:31:07.833"
}
```

#### 10.2.2 Delete User

##### Params

- id: User ID to be deleted


##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/auth/users/test
```

##### Response Status

```json
204
```

##### Response Body

```json
1
```

#### 10.2.3 Modify User

##### Params

- id: User ID to be modified

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/auth/users/test
```

##### Request Body
Modify user_name, user_password, and user_phone.

```json
{
    "user_name": "test",
    "user_password": "******",
    "user_phone": "183****9266"
}
```

##### Response Status

```json
200
```

##### Response Body
The returned result is the entire user object including the modified content.
```json
{
    "user_password": "******",
    "user_update": "2020-11-12 10:29:30.455",
    "user_name": "test",
    "user_creator": "admin",
    "user_phone": "183****9266",
    "id": "test",
    "user_create": "2020-11-12 10:27:13.601"
}
```

#### 10.2.4 Query User List

##### Params

- limit: Upper limit of the number of results returned


##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/users
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "users": [
        {
            "user_password": "******",
            "user_update": "2020-11-11 11:41:12.254",
            "user_name": "admin",
            "user_creator": "system",
            "id": "admin",
            "user_create": "2020-11-11 11:41:12.254"
        }
    ]
}
```

#### 10.2.5 Query a User

##### Params

- id: User ID to be queried

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/users/admin
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "users": [
        {
            "user_password": "******",
            "user_update": "2020-11-11 11:41:12.254",
            "user_name": "admin",
            "user_creator": "system",
            "id": "admin",
            "user_create": "2020-11-11 11:41:12.254"
        }
    ]
}
```

#### 10.2.6 Query Roles of a User

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/users/boss/role
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "roles": {
        "hugegraph": {
            "READ": [
                {
                    "type": "ALL",
                    "label": "*",
                    "properties": null
                }
            ]
        }
    }
}
```

### 10.3 Group (Group) API
Groups grant corresponding resource permissions, and users are assigned to different groups, thereby having different resource permissions.
The group interface includes APIs for creating groups, deleting groups, modifying groups, and querying group-related information.

#### 10.3.1 Create Group

##### Params

- group_name: Group name
- group_description: Group description

##### Request Body

```json
{
    "group_name": "all",
    "group_description": "group can do anything"
}
```


##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/auth/groups
```

##### Response Status

```json
201 
```

##### Response Body

```json
{
    "group_creator": "admin",
    "group_name": "all",
    "group_create": "2020-11-11 15:46:08.791",
    "group_update": "2020-11-11 15:46:08.791",
    "id": "-69:all",
    "group_description": "group can do anything"
}
```

#### 10.3.2 Delete Group

##### Params

- id: Group ID to be deleted


##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/auth/groups/-69:grant
```

##### Response Status

```json
204
```

##### Response Body

```json
1
```

#### 10.3.3 Modify Group

##### Params

- id: Group ID to be modified

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/auth/groups/-69:grant
```

##### Request Body
Modify group_description
```json
{
    "group_name": "grant",
    "group_description": "grant"
}
```

##### Response Status

```json
200
```

##### Response Body
The returned result is the entire group object including the modified content.

```json
{
    "group_creator": "admin",
    "group_name": "grant",
    "group_create": "2020-11-12 09:50:58.458",
    "group_update": "2020-11-12 09:57:58.155",
    "id": "-69:grant",
    "group_description": "grant"
}
```

#### 10.3.4 Query Group List

##### Params

- limit: Upper limit of the number of results returned

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/groups
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "groups": [
        {
            "group_creator": "admin",
            "group_name": "all",
            "group_create": "2020-11-11 15:46:08.791",
            "group_update": "2020-11-11 15:46:08.791",
            "id": "-69:all",
            "group_description": "group can do anything"
        }
    ]
}
```

#### 10.3.5 Query a Specific Group

##### Params

- id: Group ID to be queried

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/groups/-69:all
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "group_creator": "admin",
    "group_name": "all",
    "group_create": "2020-11-11 15:46:08.791",
    "group_update": "2020-11-11 15:46:08.791",
    "id": "-69:all",
    "group_description": "group can do anything"
}
```

### 10.4 Resource (Target) API
Resources describe data in the graph database, such as vertices that meet certain criteria. Each resource includes three elements: type, label, and properties. There are 18 types in total, and the combination of any label and any properties forms a resource. The internal conditions of a resource are based on the AND relationship, while the conditions between multiple resources are based on the OR relationship.  
The resource API includes creating, deleting, modifying, and querying resources.

#### 10.4.1 Create Resource

##### Params
- target_name: Name of the resource
- target_graph: Graph of the resource
- target_url: URL of the resource
- target_resources: Resource definitions (list)

target_resources can include multiple target_resource, stored in the form of a list.  
Each target_resource contains:
- type: Optional value: VERTEX, EDGE, etc. Can be filled with ALL, indicating it can be a vertex or edge.
- label: Optional value: name of a vertex or edge type. Can be filled with *, indicating any type.
- properties: Map type, can contain multiple key-value pairs of properties. Must match all property values. Property values can support conditional ranges (e.g., age: P.gte(18)). If properties are null, it means any property is allowed. If both the property name and value are '*', it also means any property is allowed.

For example, a specific resource: "target_resources": [{"type":"VERTEX","label":"person","properties":{"city":"Beijing","age":"P.gte(20)"}}]  
The resource definition means: a vertex of type 'person' with the city property set to 'Beijing' and the age property greater than or equal to 20.

##### Request Body

```json
{
    "target_name": "all",
    "target_graph": "hugegraph",
    "target_url": "127.0.0.1:8080",
    "target_resources": [
        {
            "type": "ALL"
        }
    ]
}
```

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/auth/targets
```

##### Response Status

```json
201 
```

##### Response Body

```json
{
    "target_creator": "admin",
    "target_name": "all",
    "target_url": "127.0.0.1:8080",
    "target_graph": "hugegraph",
    "target_create": "2020-11-11 15:32:01.192",
    "target_resources": [
        {
            "type": "ALL",
            "label": "*",
            "properties": null
        }
    ],
    "id": "-77:all",
    "target_update": "2020-11-11 15:32:01.192"
}
```

#### 10.4.2 Delete Resource

##### Params

- id: Resource Id to be deleted

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/auth/targets/-77:gremlin
```

##### Response Status

```json
204
```

##### Response Body

```json
1
```

#### 10.4.3 Modify Resource

##### Params

- id: Resource Id to be modified

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/auth/targets/-77:gremlin
```

##### Request Body
Modify the 'type' in the resource definition.

```json
{
    "target_name": "gremlin",
    "target_graph": "hugegraph",
    "target_url": "127.0.0.1:8080",
    "target_resources": [
        {
            "type": "NONE"
        }
    ]
}
```

##### Response Status

```json
200
```

##### Response Body
The response contains the entire target group object, including the modified content.
```json
{
    "target_creator": "admin",
    "target_name": "gremlin",
    "target_url": "127.0.0.1:8080",
    "target_graph": "hugegraph",
    "target_create": "2020-11-12 09:34:13.848",
    "target_resources": [
        {
            "type": "NONE",
            "label": "*",
            "properties": null
        }
    ],
    "id": "-77:gremlin",
    "target_update": "2020-11-12 09:37:12.780"
}
```

#### 10.4.4 Query Resource List

##### Params

- limit: Upper limit of the number of returned results.

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/targets
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "targets": [
        {
            "target_creator": "admin",
            "target_name": "all",
            "target_url": "127.0.0.1:8080",
            "target_graph": "hugegraph",
            "target_create": "2020-11-11 15:32:01.192",
            "target_resources": [
                {
                    "type": "ALL",
                    "label": "*",
                    "properties": null
                }
            ],
            "id": "-77:all",
            "target_update": "2020-11-11 15:32:01.192"
        },
        {
            "target_creator": "admin",
            "target_name": "grant",
            "target_url": "127.0.0.1:8080",
            "target_graph": "hugegraph",
            "target_create": "2020-11-11 15:43:24.841",
            "target_resources": [
                {
                    "type": "GRANT",
                    "label": "*",
                    "properties": null
                }
            ],
            "id": "-77:grant",
            "target_update": "2020-11-11 15:43:24.841"
        }
    ]
}
```

#### 10.4.5 Query a Specific Resource

##### Params

- id: Id of the resource to query

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/targets/-77:grant
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "target_creator": "admin",
    "target_name": "grant",
    "target_url": "127.0.0.1:8080",
    "target_graph": "hugegraph",
    "target_create": "2020-11-11 15:43:24.841",
    "target_resources": [
        {
            "type": "GRANT",
            "label": "*",
            "properties": null
        }
    ],
    "id": "-77:grant",
    "target_update": "2020-11-11 15:43:24.841"
}
```

### 10.5 Association of Roles (Belong) API

The association between users and user groups allows a user to be associated with one or more user groups. User groups have permissions for related resources, and the permissions for different user groups can be understood as different roles. In other words, users are associated with roles.  
The API for associating roles includes creating, deleting, modifying, and querying the association of roles for users.

#### 10.5.1 Create an Association of Roles for a User

##### Params

- user: User ID
- group: User group ID
- belong_description: Description

##### Request Body

```json
{
    "user": "boss",
    "group": "-69:all"
}
```


##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/auth/belongs
```

##### Response Status

```json
201 
```

##### Response Body

```json
{
    "belong_create": "2020-11-11 16:19:35.422",
    "belong_creator": "admin",
    "belong_update": "2020-11-11 16:19:35.422",
    "id": "Sboss>-82>>S-69:all",
    "user": "boss",
    "group": "-69:all"
}
```

#### 10.5.2 Delete an Association of Roles

##### Params

- id: ID of the association of roles to delete

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/auth/belongs/Sboss>-82>>S-69:grant
```

##### Response Status

```json
204
```

##### Response Body

```json
1
```

#### 10.5.3 Modify an Association of Roles

An association of roles can only be modified for its description. The `user` and `group` properties cannot be modified. If you need to modify an association of roles, you need to delete the existing association and create a new one.

##### Params

- id: ID of the association of roles to modify

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/auth/belongs/Sboss>-82>>S-69:grant
```

##### Request Body
Modify the `belong_description` field
```json
{
    "belong_description": "update test"
}
```

##### Response Status

```json
200
```

##### Response Body
The response includes the modified content as well as the entire association of roles object
```json
{
    "belong_description": "update test",
    "belong_create": "2020-11-12 10:40:21.720",
    "belong_creator": "admin",
    "belong_update": "2020-11-12 10:42:47.265",
    "id": "Sboss>-82>>S-69:grant",
    "user": "boss",
    "group": "-69:grant"
}
```

#### 10.5.4 Query List of Associations of Roles

##### Params

- limit: Upper limit on the number of results to return


##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/belongs
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "belongs": [
        {
            "belong_create": "2020-11-11 16:19:35.422",
            "belong_creator": "admin",
            "belong_update": "2020-11-11 16:19:35.422",
            "id": "Sboss>-82>>S-69:all",
            "user": "boss",
            "group": "-69:all"
        }
    ]
}
```

#### 10.5.5 View a Specific Association of Roles

##### Params

- id: The id of the association of roles to be queried

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/belongs/Sboss>-82>>S-69:all
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "belong_create": "2020-11-11 16:19:35.422",
    "belong_creator": "admin",
    "belong_update": "2020-11-11 16:19:35.422",
    "id": "Sboss>-82>>S-69:all",
    "user": "boss",
    "group": "-69:all"
}
```

### 10.6 Authorization (Access) API
Grant permissions to user groups for resources, including operations such as READ, WRITE, DELETE, EXECUTE, etc.
The authorization API includes: creating, deleting, modifying, and querying permissions.

#### 10.6.1 Create Authorization (Granting permissions to user groups for resources)

##### Params

- group: Group ID
- target: Resource ID
- access_permission: Permission grant
- access_description: Authorization description

Access permissions:
- READ: Read operations, including all queries such as querying the schema, retrieving vertices/edges, aggregating vertex and edge counts (VERTEX_AGGR/EDGE_AGGR), and reading the graph's status (STATUS), variables (VAR), tasks (TASK), etc.
- WRITE: Write operations, including creating and updating operations, such as adding property keys to the schema or adding/updating properties of vertices.
- DELETE: Delete operations, including deleting metadata, vertices, or edges.
- EXECUTE: Execute operations, including executing Gremlin queries, executing tasks, and executing metadata functions.

##### Request Body

```json
{
    "group": "-69:all",
    "target": "-77:all",
    "access_permission": "READ"
}
```

##### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/auth/accesses
```

##### Response Status

```json
201 
```

##### Response Body

```json
{
    "access_permission": "READ",
    "access_create": "2020-11-11 15:54:54.008",
    "id": "S-69:all>-88>11>S-77:all",
    "access_update": "2020-11-11 15:54:54.008",
    "access_creator": "admin",
  "group": "-69:all",
  "target": "-77:all"
}
```

#### 10.6.2 Delete Authorization

##### Params

- id: The ID of the authorization to be deleted

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/auth/accesses/S-69:all>-88>12>S-77:all
```

##### Response Status

```json
204
```

##### Response Body

```json
1
```

#### 10.6.3 Modify Authorization

Authorization can only be modified for its description. User group, resource, and permission cannot be modified. If you need to modify the authorization relationship, delete the original authorization and create a new one.

##### Params

- id: The ID of the authorization to be modified

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/auth/accesses/S-69:all>-88>12>S-77:all
```

##### Request Body

Modify access_description

```json
{
  "access_description": "test"
}
```

##### Response Status

```json
200
```

##### Response Body

The response includes the modified content as well as the entire authorization object.

```json
{
  "access_description": "test",
  "access_permission": "WRITE",
  "access_create": "2020-11-12 10:12:03.074",
  "id": "S-69:all>-88>12>S-77:all",
  "access_update": "2020-11-12 10:16:18.637",
  "access_creator": "admin",
  "group": "-69:all",
  "target": "-77:all"
}
```

#### 10.6.4 Query Authorization List

##### Params

- limit: The maximum number of results to return

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/accesses
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "accesses": [
    {
      "access_permission": "READ",
      "access_create": "2020-11-11 15:54:54.008",
      "id": "S-69:all>-88>11>S-77:all",
      "access_update": "2020-11-11 15:54:54.008",
      "access_creator": "admin",
      "group": "-69:all",
      "target": "-77:all"
    }
  ]
}
```

#### 10.6.5 Query a Specific Authorization

##### Params

- id: The ID of the authorization to be queried

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/auth/accesses/S-69:all>-88>11>S-77:all
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "access_permission": "READ",
  "access_create": "2020-11-11 15:54:54.008",
  "id": "S-69:all>-88>11>S-77:all",
  "access_update": "2020-11-11 15:54:54.008",
  "access_creator": "admin",
    "group": "-69:all",
    "target": "-77:all"
}
```

### 10.7 Graphspace Manager (Manager) API

> **Note**: Before using the following APIs, you need to create a graphspace first. For example, create a graphspace named `gs1` via the [Graphspace API](./graphspace). The examples below assume that `gs1` already exists.

1. The graphspace manager API is used to grant/revoke manager roles for users at the graphspace level, and to query the roles of the current user or other users in a graphspace. Supported role types include `SPACE`, `SPACE_MEMBER`, and `ADMIN`.

#### 10.7.1 Check whether the current login user has a specific role

##### Params

- type: Role type to check, optional

##### Method & Url

```
GET http://localhost:8080/graphspaces/gs1/auth/managers/check?type=WRITE
```

##### Response Status

```json
200
```

##### Response Body

```json
"true"
```

The API returns the string `true` or `false` indicating whether the current user has the given role.

#### 10.7.2 List graphspace managers

##### Params

- type: Role type, optional, used to filter by role

##### Method & Url

```
GET http://localhost:8080/graphspaces/gs1/auth/managers?type=SPACE
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "managers": [
    {
      "user": "admin",
      "type": "SPACE",
      "create_time": "2024-01-10 09:30:00"
    }
  ]
}
```

#### 10.7.3 Grant/create a graphspace manager

- The following example grants user `boss` the `SPACE_MEMBER` role in graphspace `gs1`.

##### Request Body

```json
{
  "user": "boss",
  "type": "SPACE_MEMBER"
}
```

##### Method & Url

```
POST http://localhost:8080/graphspaces/gs1/auth/managers
```

##### Response Status

```json
201
```

##### Response Body

```json
{
  "user": "boss",
  "type": "SPACE_MEMBER",
  "manager_creator": "admin",
  "manager_create": "2024-01-10 09:45:12"
}
```

#### 10.7.4 Revoke graphspace manager privileges

- The following example revokes the `SPACE_MEMBER` role of user `boss` in graphspace `gs1`.

##### Params

- user: User ID to revoke
- type: Role type to revoke

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/gs1/auth/managers?user=boss&type=SPACE_MEMBER
```

##### Response Status

```json
204
```

##### Response Body

```json
1
```

#### 10.7.5 Query roles of a specific user in a graphspace

##### Params

- user: User ID

##### Method & Url

```
GET http://localhost:8080/graphspaces/gs1/auth/managers/role?user=boss
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "roles": {
    "boss": [
      "READ",
      "SPACE_MEMBER"
    ]
  }
}
```
