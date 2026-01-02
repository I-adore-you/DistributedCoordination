# ZooKeeper Docker 集群配置说明

本文档介绍了两个不同版本的 ZooKeeper 集群 Docker 配置：
1. **ZooKeeper 3.6.3** - 静态配置节点集群
2. **ZooKeeper 3.7.0** - 支持动态配置节点集群

## 1. ZooKeeper 3.6.3（静态配置）

### 配置文件
`docker-compose-zk346.yml`（兼容3.6.3版本）
`docker-compose-zk363-static.yml`（推荐，明确标识为静态配置）

### 特点
- 使用 ZooKeeper 3.6.3 版本（原计划使用3.4.6，但由于ARM64架构支持问题，升级到3.6.3）
- 静态配置 3 个节点的集群
- 节点信息在启动前固定配置
- 不支持动态添加/删除节点
- 支持 ARM64 架构（适用于 Apple Silicon Mac）

### 启动集群
```bash
# 使用兼容版本文件
docker-compose -f docker-compose-zk346.yml up -d

# 使用推荐的明确标识为静态配置的文件（推荐）
docker-compose -f docker-compose-zk363-static.yml up -d
```

### 验证集群状态
```bash
# 检查兼容版本文件的容器状态
docker-compose -f docker-compose-zk346.yml ps

# 检查推荐版本文件的容器状态
docker-compose -f docker-compose-zk363-static.yml ps

# 查看兼容版本节点状态（主从信息）
docker exec -it zk1-3.4.6 zkServer.sh status

# 查看推荐版本节点状态（主从信息）
docker exec -it zk1-3.6.3-static zkServer.sh status
```

### 连接客户端
```bash
# 连接兼容版本客户端
docker exec -it zk1-3.4.6 zkCli.sh -server zk1:2181,zk2:2181,zk3:2181

# 连接推荐版本客户端
docker exec -it zk1-3.6.3-static zkCli.sh -server zk1:2181,zk2:2181,zk3:2181
```

### 停止集群
```bash
# 停止兼容版本集群
docker-compose -f docker-compose-zk346.yml down

# 停止推荐版本集群
docker-compose -f docker-compose-zk363-static.yml down
```

## 2. ZooKeeper 3.7.0（动态配置）

### 配置文件
`docker-compose-zk370-dynamic.yml`

### 特点
- 使用 ZooKeeper 3.7.0 版本
- 支持动态添加/删除节点
- 启用了 `reconfig` 功能
- 配置了动态配置文件 `zoo.cfg.dynamic`
- 包含一个可选的第4个节点用于演示动态添加

### 启动基础集群（3个节点）
```bash
docker-compose -f docker-compose-zk370-dynamic.yml up -d
```

### 启动包含可选节点的集群
```bash
docker-compose -f docker-compose-zk370-dynamic.yml --profile optional up -d
```

### 验证集群状态
```bash
docker-compose -f docker-compose-zk370-dynamic.yml ps
```

### 演示动态配置功能

#### 1. 连接到 ZK 客户端
```bash
docker exec -it zk1-3.7.0-dynamic zkCli.sh -server zk1:2181
```

#### 2. 查看当前集群配置
```bash
# 在 ZK 客户端中执行
reconfig -display
```

#### 3. 动态添加节点 zk4
```bash
# 在 ZK 客户端中执行
reconfig -add server.4=zk4:2888:3888:participant;2181
```

#### 4. 动态移除节点 zk4
```bash
# 在 ZK 客户端中执行
reconfig -remove 4
```

### 停止集群
```bash
docker-compose -f docker-compose-zk370-dynamic.yml down
```

## 3. 版本差异对比

| 特性 | ZooKeeper 3.6.3 | ZooKeeper 3.7.0 |
|------|----------------|-----------------|
| 配置方式 | 静态配置 | 支持静态和动态配置 |
| reconfig 命令 | 支持但默认禁用 | 支持且默认启用 |
| 动态配置文件 | 支持 | zoo.cfg.dynamic |
| 节点角色 | participant/observer | participant/observer |
| 4LW 命令 | 基本命令 + reconfig | 增加更多管理命令 |
| 管理界面 | 内置 AdminServer (8080端口) | 内置 AdminServer (8080端口) |
| 配置更新 | 需要重启节点（静态配置） | 实时生效（动态配置） |
| ARM64 支持 | 支持 | 支持 |

## 4. 网络配置

| 集群版本 | 网络名称 | IP 子网 | 节点 IP 范围 |
|---------|---------|--------|-------------|
| 3.6.3（兼容文件） | zk346-net | 192.168.160.0/24 | 192.168.160.11-13 |
| 3.6.3（推荐文件） | zk363-static-net | 192.168.161.0/24 | 192.168.161.11-13 |
| 3.7.0 | zk370-dynamic-net | 192.168.170.0/24 | 192.168.170.11-14 |

## 5. 端口映射

### 3.6.3 集群（兼容文件）
- zk1: 2181 → 2181
- zk2: 2182 → 2181
- zk3: 2183 → 2181

### 3.6.3 集群（推荐文件）
- zk1: 2181 → 2181
- zk2: 2182 → 2181
- zk3: 2183 → 2181

### 3.7.0 集群
- zk1: 2181 → 2181, 8080 → 8080
- zk2: 2182 → 2181, 8081 → 8080
- zk3: 2183 → 2181, 8082 → 8080
- zk4 (可选): 2184 → 2181, 8083 → 8080

## 6. 数据持久化

集群将数据持久化到以下目录：
- 3.6.3 集群（兼容文件）: `./zk346/zk*/data`
- 3.6.3 集群（推荐文件）: `./zk363-static/zk*/data`
- 3.7.0 集群: `./zk370-dynamic/zk*/data`

## 7. 注意事项

1. **端口冲突**：确保本地端口 2181-2184 和 8080-8083 未被占用
2. **内存需求**：每个 ZooKeeper 节点至少需要 256MB 内存
3. **首次启动**：集群首次启动可能需要 10-30 秒进行初始化
4. **动态配置权限**：在生产环境中，应限制 reconfig 命令的使用权限
5. **版本兼容性**：3.6.3 和 3.7.0 之间存在配置文件格式差异
6. **ARM64 支持**：3.6.3 和 3.7.0 版本都支持 ARM64 架构（适用于 Apple Silicon Mac）
7. **静态配置说明**：3.6.3 版本的静态配置集群虽然支持 reconfig 命令，但默认未启用动态配置功能

## 8. 管理界面

3.6.3 和 3.7.0 集群都提供了内置的 AdminServer 管理界面：

### 3.6.3 集群（推荐文件）
- zk1: http://localhost:8080
- zk2: http://localhost:8081
- zk3: http://localhost:8082

### 3.7.0 集群
- zk1: http://localhost:8080
- zk2: http://localhost:8081
- zk3: http://localhost:8082
- zk4: http://localhost:8083

## 9. 测试命令

### 查看集群状态
```bash
# 3.6.3（兼容文件）
docker exec -it zk1-3.4.6 zkServer.sh status

# 3.6.3（推荐文件）
docker exec -it zk1-3.6.3-static zkServer.sh status

# 3.7.0
docker exec -it zk1-3.7.0-dynamic zkServer.sh status
```

### 检查节点健康
```bash
# 使用 ruok 命令（所有版本都支持）
docker exec -it zk1-3.4.6 echo ruok | nc localhost 2181  # 兼容文件
docker exec -it zk1-3.6.3-static echo ruok | nc localhost 2181  # 推荐文件
docker exec -it zk1-3.7.0-dynamic echo ruok | nc localhost 2181  # 3.7.0 集群
```

### 查看集群配置详情
```bash
# 使用 conf 命令（所有版本都支持）
docker exec -it zk1-3.4.6 echo conf | nc localhost 2181  # 兼容文件
docker exec -it zk1-3.6.3-static echo conf | nc localhost 2181  # 推荐文件
docker exec -it zk1-3.7.0-dynamic echo conf | nc localhost 2181  # 3.7.0 集群
```

## 10. 清理资源

### 删除所有容器和网络
```bash
docker-compose -f docker-compose-zk346.yml down  # 兼容文件
docker-compose -f docker-compose-zk363-static.yml down  # 推荐文件
docker-compose -f docker-compose-zk370-dynamic.yml down  # 3.7.0 集群
```

### 删除所有数据
```bash
rm -rf ./zk346 ./zk363-static ./zk370-dynamic
```

## 总结

- **3.6.3 版本**适合需要稳定、简单配置的场景，不支持动态扩展（静态配置）
- **3.7.0 版本**适合需要灵活扩展的场景，支持动态添加/删除节点
- 两个版本可以同时运行，使用不同的网络和端口
- 3.6.3 和 3.7.0 版本都支持 ARM64 架构，适合在 Apple Silicon Mac 上运行
- 动态配置功能需要谨慎使用，建议在测试环境中充分验证后再应用于生产环境
