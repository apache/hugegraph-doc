# HugeGraph工具链本地测试指南

LLMS 索引： [llms.txt](/versions/1.7/cn/llms.txt)

---

本指南帮助开发者在本地运行 HugeGraph 工具链测试。

## 1. 核心概念

### 1.1 核心依赖：HugeGraph Server

**工具链的集成测试和功能测试都依赖 HugeGraph Server**，包括 Client、Loader、Hubble、Spark Connector、Tools 等组件。

### 1.2 测试类型

- **单元测试 (Unit Tests)**：测试单个函数/方法，不依赖外部服务
- **API 测试 (ApiTestSuite)**：测试 API 接口，需要运行中的 HugeGraph Server
- **功能测试 (FuncTestSuite)**：端到端测试，需要完整的系统环境

## 2. 环境准备

### 2.1 系统要求

- **操作系统**：Linux / macOS（Windows 使用 WSL2）
- **JDK**：>= 11，配置好 `JAVA_HOME`
- **Maven**：>= 3.6
- **Python**：>= 3.11（仅 Hubble 测试需要）

### 2.2 克隆代码

```bash
git clone https://github.com/apache/hugegraph-toolchain.git
cd hugegraph-toolchain
```

## 3. 部署测试环境

### 方式选择

- **脚本部署**：指定 Server Commit，可复现 CI 使用的服务端版本
- **Docker 部署**：适合快速检查；测试失败时应先核对镜像与 Toolchain 的兼容性

> 详细安装说明参考 [社区文档](https://hugegraph.apache.org/versions/1.7/cn/docs/quickstart/hugegraph/hugegraph-server/)

### 3.1 脚本部署

#### 参数说明

- **`$COMMIT_ID`**：指定 Server 源码的 Git Commit ID
- **`$DB_DATABASE` / `$DB_PASS`**：Loader JDBC 测试用的 MySQL 数据库名和密码

#### 部署步骤

**1. 安装 HugeGraph Server**

```bash
# 设置 Server 基线；需要可复现结果时请使用完整 commit SHA
export COMMIT_ID="master"

# 执行安装（脚本位于 /assembly/travis/ 目录）
hugegraph-client/assembly/travis/install-hugegraph-from-source.sh $COMMIT_ID
```

- 脚本会启动 HTTP 8080 和 HTTPS 8443 两个实例，并配置 `admin`/`pa` 认证。
- 执行前确认两个端口未被占用。

**2. 安装可选依赖**

```bash
# Hadoop (仅 Loader HDFS 测试需要)
hugegraph-loader/assembly/travis/install-hadoop.sh

# MySQL (仅 Loader JDBC 测试需要)
hugegraph-loader/assembly/travis/install-mysql.sh $DB_DATABASE $DB_PASS
```

**3. 健康检查**

```bash
curl -u admin:pa http://localhost:8080/graphspaces/DEFAULT/graphs
# 返回 {"graphs":["hugegraph"]} 表示成功
```

### 3.2 Docker 部署

> **注意**：Docker 镜像可能版本滞后，如遇兼容性问题请使用脚本部署

#### 快速启动

```bash
docker network create hugegraph-net
docker run -itd --name=server -p 8080:8080 --network hugegraph-net hugegraph/hugegraph:latest
```

#### docker-compose 配置（可选）

完整配置示例，包含 Server、MySQL、Hadoop 服务（需要 Docker Compose V2）：

```yaml
version: '3.8'

services:
  hugegraph-server:
    image: hugegraph/hugegraph:latest  # 可以替换为特定版本，或构建自己的镜像
    container_name: hugegraph-server
    ports:
      - "8080:8080"  # HugeGraph Server HTTP 端口
    environment:
      # 根据需要配置HugeGraph Server的参数，例如后端存储
      - HUGEGRAPH_SERVER_OPTIONS="-Dstore.backend=rocksdb"
    volumes:
      # 如果需要持久化数据或挂载配置文件，可以在这里添加卷
      # - ./hugegraph-data:/opt/hugegraph/data
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/graphspaces/DEFAULT/graphs || exit 1"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - hugegraph-net
  
  # 如果需要hugegraph-loader的JDBC测试，可以添加以下服务
  #   mysql:
  #     image: mysql:5.7
  #     container_name: mysql-db
  #     environment:
  #       MYSQL_ROOT_PASSWORD: ${DB_PASS:-your_mysql_root_password} # 从环境变量读取，或使用默认值
  #       MYSQL_DATABASE: ${DB_DATABASE:-hugegraph_test_db} # 从环境变量读取，或使用默认值
  #     ports:
  #       - "3306:3306"
  #     volumes:
  #       - ./mysql-data:/var/lib/mysql # 数据持久化
  #     healthcheck:
  #       test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-p${DB_PASS:-your_mysql_root_password}"]
  #       interval: 5s
  #       timeout: 3s
  #       retries: 5
  #     networks:
  #       - hugegraph-net

  # 如果需要hugegraph-loader的Hadoop/HDFS测试，可以添加以下服务
  #   namenode:
  #     image: johannestang/hadoop-namenode:2.0.0-hadoop2.8.5-java8
  #     container_name: namenode
  #     ports:
  #       - "0.0.0.0:9870:9870"
  #       - "0.0.0.0:8020:8020"
  #     environment:
  #       - CLUSTER_NAME=test-cluster
  #       - HDFS_NAMENODE_USER=root
  #       - HADOOP_CONF_DIR=/hadoop/etc/hadoop
  #     volumes:
  #       - ./config/core-site.xml:/hadoop/etc/hadoop/core-site.xml
  #       - ./config/hdfs-site.xml:/hadoop/etc/hadoop/hdfs-site.xml
  #       - namenode_data:/hadoop/dfs/name
  #     command: bash -c "if [ ! -d /hadoop/dfs/name/current ]; then hdfs namenode -format; fi && /entrypoint.sh"
  #     healthcheck:
  #       test: ["CMD", "hdfs", "dfsadmin", "-report"]
  #       interval: 5s
  #       timeout: 3s
  #       retries: 5
  #     networks:
  #       - hugegraph-net

  #   datanode:
  #     image: johannestang/hadoop-datanode:2.0.0-hadoop2.8.5-java8
  #     container_name: datanode
  #     depends_on:
  #       - namenode
  #     environment:
  #       - CLUSTER_NAME=test-cluster
  #       - HDFS_DATANODE_USER=root
  #       - HADOOP_CONF_DIR=/hadoop/etc/hadoop
  #     volumes:
  #       - ./config/core-site.xml:/hadoop/etc/hadoop/core-site.xml
  #       - ./config/hdfs-site.xml:/hadoop/etc/hadoop/hdfs-site.xml
  #       - datanode_data:/hadoop/dfs/data
  #     healthcheck:
  #       test: ["CMD", "hdfs", "dfsadmin", "-report"]
  #       interval: 5s
  #       timeout: 3s
  #       retries: 5
  #     networks:
  #       - hugegraph-net

networks:
  hugegraph-net:
    driver: bridge
volumes:
  namenode_data:
  datanode_data:
```

#### Hadoop 配置挂载
在与 `docker-compose.yml` 相同的目录下创建 `./config` 文件夹用于挂载 Hadoop 配置文件。如果不需要 HDFS 测试，可以跳过此步骤。

📁 ./config/core-site.xml 内容：

```xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://namenode:8020</value>
    </property>
</configuration>
```

📁 ./config/hdfs-site.xml 内容：

```xml
<configuration>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>/hadoop/hdfs/name</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>/hadoop/hdfs/data</value>
    </property>
    <property>
        <name>dfs.permissions.superusergroup</name>
        <value>hadoop</value>
    </property>
    <property>
        <name>dfs.support.append</name>
        <value>true</value>
    </property>
</configuration>
```

#### Docker 操作

```bash
# 启动服务
docker compose up -d

# 检查状态
docker compose ps
lsof -i:8080  # Server
lsof -i:8020  # Hadoop
lsof -i:3306  # MySQL

# 停止服务
docker compose down
```

## 4. 运行测试

各工具的测试流程：

<div style="text-align: center;">
    <img src="/versions/1.7/docs/images/toolchain-test-mermaid-2.png" alt="HugeGraph工具链测试流程图">
</div>

### 4.1 hugegraph-client

#### 编译

```bash
mvn -e compile -pl hugegraph-client -Dmaven.javadoc.skip=true -ntp
```

#### 依赖服务

启动 HugeGraph Server（参考 [第3节](#3-部署测试环境)）

##### Server 鉴权配置

ApiTest 需要认证。使用 3.1 节的脚本安装时无需重复配置；自行部署 Server 时，认证配置和测试凭证必须与测试代码一致。

```bash
# 1. 修改鉴权模式
cp conf/rest-server.properties conf/rest-server.properties.backup
sed -i 's|#auth.authenticator=.*|auth.authenticator=org.apache.hugegraph.auth.StandardAuthenticator|' conf/rest-server.properties
grep auth.authenticator conf/rest-server.properties
sed -i 's|gremlin.graph=org.apache.hugegraph.HugeFactory|gremlin.graph=org.apache.hugegraph.auth.HugeFactoryAuthProxy|' conf/graphs/hugegraph.properties

# 2. 设置密码
# 注：测试代码中默认使用 "pa" 作为密码，设置时需与测试保持一致
bin/stop-hugegraph.sh
export PASSWORD="pa"  # 设置为测试默认密码
echo -e "${PASSWORD}" | bin/init-store.sh
bin/start-hugegraph.sh
```

#### 运行测试

```bash
# 检查环境
curl -u admin:pa http://localhost:8080/graphspaces/DEFAULT/graphs

# 运行测试
cd hugegraph-client
mvn test -Dtest=UnitTestSuite -ntp      # 单元测试
mvn test -Dtest=ApiTestSuite -ntp       # API测试（需 Server）
mvn test -Dtest=FuncTestSuite -ntp      # 功能测试（需 Server）
```

> 测试失败时检查 Server 日志：`logs/hugegraph-server.log`

### 4.2 hugegraph-loader

#### 编译

```bash
mvn install -pl hugegraph-client,hugegraph-loader -am -Dmaven.javadoc.skip=true -DskipTests -ntp
```

#### 依赖服务

- **必需**：HugeGraph Server
- **可选**：Hadoop (HDFS 测试)、MySQL (JDBC 测试)

#### 运行测试

```bash
cd hugegraph-loader
mvn test -P unit -ntp   # 单元测试
mvn test -P file -ntp   # 文件测试（需 Server）
mvn test -P hdfs -ntp   # HDFS测试（需 Server + Hadoop）
mvn test -P jdbc -ntp   # JDBC测试（需 Server + MySQL）
mvn test -P kafka -ntp  # Kafka测试（需 Server）
```

### 4.3 hugegraph-hubble

#### 编译

```bash
mvn install -pl hugegraph-client,hugegraph-loader -am -Dmaven.javadoc.skip=true -DskipTests -ntp
cd hugegraph-hubble
mvn -e compile -Dmaven.javadoc.skip=true -ntp
```

#### 依赖服务

**1. 启动 Server**（参考 [第3节](#3-部署测试环境)）

**2. Python 环境**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
python -m pip install -r hubble-dist/assembly/travis/requirements.txt
```

**3. 构建并验证**

```bash
mvn package -Dmaven.test.skip=true
# 可选：启动验证
cd apache-hugegraph-hubble*/bin
./start-hubble.sh -d && sleep 10
curl http://localhost:8088/actuator/health
./stop-hubble.sh
```

#### 运行测试

```bash
# 单元测试
mvn test -P unit-test -pl hugegraph-hubble/hubble-be -ntp

# 旧版 Python API 测试（需 Server；脚本会安装并启动 Hubble）
curl -u admin:pa http://localhost:8080/graphspaces/DEFAULT/graphs  # 检查 Server
cd hugegraph-hubble
./hubble-dist/assembly/travis/run-api-test.sh

# 当前 CI 的完整验收入口（需先生成 Hubble tar 包）
HUBBLE_TARBALL="$(ls target/apache-hugegraph-hubble-*.tar.gz | head -n 1)"
hubble-dist/assembly/travis/verify-hubble-issue-694.sh \
  "$HUBBLE_TARBALL" http://127.0.0.1:8080
```

### 4.4 hugegraph-spark-connector

#### 编译

```bash
mvn install -pl hugegraph-client,hugegraph-spark-connector -am -Dmaven.javadoc.skip=true -DskipTests -ntp
```

#### 运行测试

```bash
cd hugegraph-spark-connector
mvn test -ntp  # 需 Server 运行
```

### 4.5 hugegraph-tools

#### 编译

```bash
mvn install -pl hugegraph-client,hugegraph-tools -am -Dmaven.javadoc.skip=true -DskipTests -ntp
```

#### 运行测试

```bash
cd hugegraph-tools
mvn test -Dtest=FuncTestSuite -ntp  # 需 Server 运行
```

## 5. 常见问题

### 服务连接问题

无法连接 Server、MySQL 或 Hadoop 时：

- 确认服务已启动（Server 必须在 8080 端口）
- 检查端口占用：`lsof -i:8080`
- Docker 检查：`docker compose ps` 和 `docker compose logs`

### 配置问题

找不到文件或参数错误时：
- 检查环境变量：`echo $COMMIT_ID`
- 脚本权限：`chmod +x hugegraph-*/assembly/travis/*.sh`

### HDFS 测试失败

- 确认 NameNode/DataNode 运行正常
- 检查 Hadoop 日志
- 验证 HDFS 连接：`hdfs dfsadmin -report`

### JDBC 测试失败

- 确认 MySQL 运行正常
- 验证数据库连接：`mysql -u root -p$DB_PASS`
- 检查 MySQL 日志

## 6. 参考资料

- **HugeGraph GitHub 仓库**：[https://github.com/apache/hugegraph](https://github.com/apache/hugegraph)
- **HugeGraph 工具链 GitHub 仓库**：[https://github.com/apache/hugegraph-toolchain](https://github.com/apache/hugegraph-toolchain)
- **HugeGraph Server 文档**：[https://hugegraph.apache.org/cn/docs/quickstart/hugegraph/hugegraph-server/](https://hugegraph.apache.org/versions/1.7/cn/docs/quickstart/hugegraph/hugegraph-server/)
- **CI 配置**：`.github/workflows/*-ci.yml`
- **依赖服务安装脚本**：`hugegraph-*/assembly/travis/`
