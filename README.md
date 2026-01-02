# ZooKeeper 学习与实践项目

[![Java](https://img.shields.io/badge/Java-1.8+-orange.svg)](https://www.oracle.com/java/)
[![ZooKeeper](https://img.shields.io/badge/ZooKeeper-3.4.6%2F3.6.3%2F3.7.0-blue.svg)](https://zookeeper.apache.org/)
[![Maven](https://img.shields.io/badge/Maven-3.6+-red.svg)](https://maven.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)

这是一个 ZooKeeper 学习与实践项目，包含 ZooKeeper 客户端操作示例、分布式锁实现、配置中心应用场景以及 Docker 集群部署配置。

## 📚 项目简介

本项目旨在通过实践学习 ZooKeeper 的核心概念和应用场景，包括：

- **ZooKeeper 客户端操作**：基本 API 使用、Watch 机制、异步回调等
- **分布式锁实现**：基于 ZooKeeper 的分布式锁实现
- **配置中心**：使用 ZooKeeper 实现分布式配置管理
- **集群部署**：Docker Compose 方式部署不同版本的 ZooKeeper 集群
- **动态扩缩容**：ZooKeeper 3.7.0 动态配置节点集群

## ✨ 功能特性

- ✅ ZooKeeper 客户端基础操作示例
- ✅ Watch 监听机制实践
- ✅ 分布式锁实现（基于 ZooKeeper）
- ✅ 配置中心实现（分布式配置管理）
- ✅ Docker Compose 集群部署（支持多版本）
- ✅ 静态配置集群（ZooKeeper 3.6.3）
- ✅ 动态配置集群（ZooKeeper 3.7.0）
- ✅ 集群状态检查脚本

## 🏗️ 项目结构

```
Zookeeper-study/
├── src/main/java/com/msb/zookeeper/
│   ├── App.java                          # ZooKeeper 客户端基础示例
│   ├── config/                           # 配置管理相关类
│   │   ├── DefaultWatch.java
│   │   ├── MyConf.java
│   │   ├── TestConfig.java
│   │   ├── WatchCallBack.java
│   │   └── ZKUtils.java
│   ├── configurationcenter/              # 配置中心实现
│   │   ├── DefaultWatch.java
│   │   ├── MyConf.java
│   │   ├── TestZK.java
│   │   ├── WatchCallBack.java
│   │   ├── ZKConf.java
│   │   └── ZKUtils.java
│   ├── lock/                             # 分布式锁实现（版本1）
│   │   ├── TestLock.java
│   │   └── WatchCallBack.java
│   └── locks/                            # 分布式锁实现（版本2）
│       ├── TestLock.java
│       └── WatchCallBack.java
├── docker-compose.yml                    # 基础 Docker Compose 配置
├── docker-compose-zk346.yml             # ZooKeeper 3.4.6 集群配置
├── docker-compose-zk363-static.yml     # ZooKeeper 3.6.3 静态配置集群
├── docker-compose-zk370-dynamic.yml     # ZooKeeper 3.7.0 动态配置集群
├── check-cluster.sh                      # 集群状态检查脚本
├── check-all-nodes.sh                    # 所有节点状态检查脚本
├── ZOOKEEPER-客户端操作指南.md           # 客户端操作详细文档
├── ZooKeeper动态扩缩容机制分析.md        # 动态扩缩容机制分析
├── ZooKeeper实际应用场景-配置中心与注册中心.md  # 应用场景文档
└── README-ZK-DOCKER.md                   # Docker 部署详细文档
```

## 🚀 快速开始

### 环境要求

- JDK 1.8+
- Maven 3.6+
- Docker & Docker Compose（用于集群部署）

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd Zookeeper-study
```

### 2. 编译项目

```bash
mvn clean compile
```

### 3. 启动 ZooKeeper 集群

#### 方式一：使用静态配置集群（ZooKeeper 3.6.3）

```bash
# 启动集群
docker-compose -f docker-compose-zk363-static.yml up -d

# 查看集群状态
docker-compose -f docker-compose-zk363-static.yml ps

# 检查节点状态
./check-cluster.sh
```

#### 方式二：使用动态配置集群（ZooKeeper 3.7.0）

```bash
# 启动集群
docker-compose -f docker-compose-zk370-dynamic.yml up -d

# 查看集群状态
docker-compose -f docker-compose-zk370-dynamic.yml ps

# 检查所有节点状态
./check-all-nodes.sh
```

### 4. 运行示例代码

#### 基础客户端操作示例

```bash
# 修改 App.java 中的 ZooKeeper 连接地址
# 然后运行
mvn exec:java -Dexec.mainClass="com.msb.zookeeper.App"
```

#### 配置中心示例

```bash
mvn exec:java -Dexec.mainClass="com.msb.zookeeper.configurationcenter.TestZK"
```

#### 分布式锁示例

```bash
mvn exec:java -Dexec.mainClass="com.msb.zookeeper.locks.TestLock"
```

## 📖 核心知识点

### 1. CAP 定理

- **Consistency（一致性）**：所有节点在同一时间看到相同的数据
- **Availability（可用性）**：每个请求都能得到响应
- **Partition tolerance（分区容错性）**：系统在网络分区情况下仍能工作

ZooKeeper 保证的是 **CP**（一致性和分区容错性）。

### 2. BASE 定理

- **Basically Available（基本可用）**
- **Soft state（软状态）**
- **Eventually consistent（最终一致性）**

### 3. PAXOS 算法

ZooKeeper 使用 ZAB（ZooKeeper Atomic Broadcast）协议，它是 PAXOS 算法的一个变种。

### 4. Watch 机制

ZooKeeper 的 Watch 机制允许客户端在节点发生变化时收到通知：

- **一次性触发**：Watch 触发后需要重新注册
- **异步通知**：Watch 通知是异步的
- **顺序保证**：客户端会按照事件发生的顺序收到通知

## 🔧 Docker 集群部署

详细部署说明请参考：[README-ZK-DOCKER.md](./README-ZK-DOCKER.md)

### 快速部署命令

```bash
# 静态配置集群（推荐用于学习）
docker-compose -f docker-compose-zk363-static.yml up -d

# 动态配置集群（支持动态扩缩容）
docker-compose -f docker-compose-zk370-dynamic.yml up -d
```

### 连接客户端

```bash
# 连接静态配置集群
docker exec -it zk1-3.6.3-static zkCli.sh -server zk1:2181,zk2:2181,zk3:2181

# 连接动态配置集群
docker exec -it zk1-3.7.0-dynamic zkCli.sh -server zk1:2181,zk2:2181,zk3:2181
```

## 📝 相关文档

- [ZOOKEEPER-客户端操作指南.md](./ZOOKEEPER-客户端操作指南.md) - 详细的客户端操作文档
- [ZooKeeper动态扩缩容机制分析.md](./ZooKeeper动态扩缩容机制分析.md) - 动态扩缩容机制分析
- [ZooKeeper实际应用场景-配置中心与注册中心.md](./ZooKeeper实际应用场景-配置中心与注册中心.md) - 实际应用场景分析
- [README-ZK-DOCKER.md](./README-ZK-DOCKER.md) - Docker 部署详细文档

## 🛠️ 技术栈

- **Java** - 编程语言
- **ZooKeeper** - 分布式协调服务
  - 版本：3.4.6 / 3.6.3 / 3.7.0
- **Maven** - 项目构建工具
- **Docker** - 容器化部署
- **Docker Compose** - 容器编排

## 📦 依赖

主要依赖：

```xml
<dependency>
    <groupId>org.apache.zookeeper</groupId>
    <artifactId>zookeeper</artifactId>
    <version>3.4.6</version>
</dependency>
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目仅用于学习目的。

## 📧 联系方式

如有问题或建议，欢迎通过 Issue 反馈。

---

**注意**：本项目主要用于学习和实践 ZooKeeper，生产环境使用请参考官方文档和最佳实践。
