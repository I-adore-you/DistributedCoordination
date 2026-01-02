# ZooKeeper 客户端连接和命令操作指南

本文档详细介绍如何连接 ZooKeeper 集群以及常用的客户端命令操作，适用于 API 学习和分布式协调学习。

## 目录
1. [启动集群](#1-启动集群)
2. [客户端连接方式](#2-客户端连接方式)
3. [基本命令操作](#3-基本命令操作)
4. [节点类型和特性](#4-节点类型和特性)
5. [Watch 机制](#5-watch-机制)
6. [ACL 权限控制](#6-acl-权限控制)
7. [集群管理命令](#7-集群管理命令)
8. [Java API 示例](#8-java-api-示例)
9. [常见使用场景](#9-常见使用场景)

---

## 1. 启动集群

### 1.1 启动 3.6.3 静态配置集群（使用 zk346 目录）
```bash
docker-compose -f docker-compose-zk346.yml up -d
```

### 1.2 启动 3.6.3 静态配置集群（使用 zk363-static 目录）
```bash
docker-compose -f docker-compose-zk363-static.yml up -d
```

### 1.3 启动 3.7.0 动态配置集群
```bash
docker-compose -f docker-compose-zk370-dynamic.yml up -d
```

### 1.4 验证集群状态
```bash
# 查看容器状态
docker-compose -f docker-compose-zk346.yml ps

# 查看节点状态（Leader/Follower）
docker exec -it zk1-3.4.6 zkServer.sh status
docker exec -it zk2-3.4.6 zkServer.sh status
docker exec -it zk3-3.4.6 zkServer.sh status
```

---

## 2. 客户端连接方式

### 2.1 使用 zkCli.sh 命令行客户端（推荐学习使用）

#### 连接单个节点
```bash
# 连接 zk1
docker exec -it zk1-3.4.6 zkCli.sh -server zk1:2181

# 连接 zk2
docker exec -it zk2-3.4.6 zkCli.sh -server zk2:2181

# 连接 zk3
docker exec -it zk3-3.4.6 zkCli.sh -server zk3:2181
```

#### 连接集群（自动故障转移）
```bash
# 连接整个集群，客户端会自动选择可用的节点
docker exec -it zk1-3.4.6 zkCli.sh -server zk1:2181,zk2:2181,zk3:2181
```

#### 从宿主机连接（如果端口已映射）
```bash
# 使用本地端口连接
zkCli.sh -server localhost:2181,localhost:2182,localhost:2183
```

### 2.2 使用 Java API 连接

```java
import org.apache.zookeeper.ZooKeeper;
import java.util.concurrent.CountDownLatch;

// 连接字符串：多个节点用逗号分隔
String connectString = "192.168.160.11:2181,192.168.160.12:2181,192.168.160.13:2181";
int sessionTimeout = 3000; // 会话超时时间（毫秒）

ZooKeeper zk = new ZooKeeper(connectString, sessionTimeout, new Watcher() {
    @Override
    public void process(WatchedEvent event) {
        System.out.println("事件: " + event);
    }
});
```

---

## 3. 基本命令操作

### 3.1 帮助命令
```bash
# 查看所有命令
help

# 查看特定命令帮助
help create
help get
```

### 3.2 节点创建（create）

#### 创建持久节点
```bash
# 创建持久节点
create /test "data"

# 创建持久节点并指定数据
create /app/config "{\"key\":\"value\"}"

# 创建多级路径（需要先创建父节点）
# 错误示例：如果 /parent 不存在，会报错 "Node does not exist"
create /parent/child "child data"
# 错误信息：Node does not exist: /parent/child

# 正确方法：先创建父节点，再创建子节点
create /parent "parent data"
create /parent/child "child data"

# 或者创建空父节点
create /parent ""
create /parent/child "child data"
```

**重要提示**：
- ZooKeeper **不会自动创建父节点**，必须手动逐级创建
- 如果父节点不存在，创建子节点会报错：`Node does not exist: /path/to/node`
- 创建多级路径时，需要从根节点开始逐级创建

#### 创建临时节点（EPHEMERAL）
```bash
# 临时节点：客户端断开连接后自动删除
create -e /ephemeral-node "temp data"
```

**临时节点删除机制详解：**

临时节点不是立即删除的，而是基于会话（Session）机制：

1. **删除时机**：
   - 当客户端**会话过期（Session Expired）**时，临时节点才会被删除
   - 会话过期时间 = 会话超时时间（Session Timeout），默认通常是 30-40 秒

2. **会话机制**：
   - 客户端连接 ZooKeeper 时会创建一个会话
   - 会话有超时时间（Session Timeout），默认值通常是 30000 毫秒（30秒）
   - 客户端需要定期发送心跳（Heartbeat）来保持会话活跃

3. **心跳机制**：
   - 客户端每 `tickTime`（默认 2 秒）发送一次心跳
   - 如果服务器在 `sessionTimeout` 时间内没有收到客户端心跳，会话过期
   - 会话过期后，该会话创建的所有临时节点会被删除

4. **实际行为示例**：
   ```bash
   # 客户端1：创建临时节点
   create -e /temp-node "data"
   
   # 客户端1：正常断开连接（quit 或 close）
   # → 会话立即关闭，临时节点立即删除
   
   # 客户端1：网络断开或进程崩溃
   # → 服务器等待 sessionTimeout（如30秒）后删除临时节点
   
   # 客户端1：进程挂起（不发送心跳）
   # → 服务器等待 sessionTimeout 后删除临时节点
   ```

5. **立即删除 vs 延迟删除**：
   - **立即删除**：客户端主动关闭连接（`quit`、`close()`），会话立即关闭，临时节点立即删除
   - **延迟删除**：客户端异常断开（网络故障、进程崩溃），服务器等待 `sessionTimeout` 后删除临时节点

6. **查看会话信息**：
   ```bash
   # 查看节点的 ephemeralOwner（临时节点所有者会话ID）
   get -s /temp-node
   # ephemeralOwner = 0x100000488b80002  # 非零值表示临时节点
   
   # 查看会话信息（需要管理员权限）
   echo dump | nc localhost 2181
   ```

**重要提示**：
- 临时节点的删除依赖于会话状态，不是连接状态
- 会话超时时间是可配置的，创建连接时可以设置
- 如果客户端网络不稳定，临时节点可能会因为会话过期而被误删

#### 创建顺序节点（SEQUENTIAL）
```bash
# 顺序节点：ZooKeeper 会自动在节点名后添加递增序号
create -s /sequential-node "data"
# 结果：/sequential-node0000000001

create -s /app/task "task data"
# 结果：/app/task0000000002
```

#### 创建临时顺序节点（EPHEMERAL_SEQUENTIAL）
```bash
# 临时顺序节点：结合临时和顺序特性
create -e -s /lock "lock data"
# 结果：/lock0000000003
```

### 3.3 节点查询（get, ls, stat）

#### 获取节点数据
```bash
# 获取节点数据
get /test

# 获取节点数据并注册 Watch
get /test watch

# 获取节点数据（不注册 Watch）
get /test false
```

#### 列出子节点
```bash
# 列出直接子节点
ls /

# 列出子节点并注册 Watch
ls / watch

# 递归列出所有子节点（3.5.0+）
ls -R /
```

#### 查看节点状态信息
```bash
# 查看节点详细信息（不获取数据）
stat /test

# 查看节点状态并注册 Watch
stat /test watch
```

**stat 输出说明（详细解释）：**

| 字段 | 说明 | 示例值 | 详细解释 |
|------|------|--------|----------|
| **cZxid** | 创建事务ID | `0x50000000b` | ZooKeeper 事务ID（Zxid），节点创建时的事务ID。Zxid 是全局递增的64位整数，用于保证操作的顺序性 |
| **ctime** | 创建时间 | `Fri Jan 02 06:27:27 UTC 2026` | 节点创建的时间戳（UTC时间） |
| **mZxid** | 修改事务ID | `0x50000000b` | 节点数据最后一次修改时的事务ID。如果等于 cZxid，说明节点创建后数据未被修改 |
| **mtime** | 修改时间 | `Fri Jan 02 06:27:27 UTC 2026` | 节点数据最后一次修改的时间戳（UTC时间） |
| **pZxid** | 子节点变更事务ID | `0x50000000c` | 该节点的子节点列表最后一次修改时的事务ID。用于跟踪子节点的创建和删除 |
| **cversion** | 子节点版本号 | `1` | 子节点版本号，每次子节点创建或删除时递增。用于乐观锁控制子节点操作 |
| **dataVersion** | 数据版本号 | `0` | 节点数据版本号，每次数据修改时递增。用于乐观锁控制数据修改（setData） |
| **aclVersion** | ACL版本号 | `0` | ACL（访问控制列表）版本号，每次 ACL 修改时递增。用于乐观锁控制权限修改 |
| **ephemeralOwner** | 临时节点所有者 | `0x0` | 临时节点的所有者会话ID。如果是持久节点，值为 `0x0`（0）；如果是临时节点，值为创建该节点的客户端会话ID |
| **dataLength** | 数据长度 | `0` | 节点数据的字节长度。如果节点数据为空，值为 0 |
| **numChildren** | 子节点数量 | `1` | 该节点直接子节点的数量（不包括孙子节点） |

**实际示例解析：**

```bash
[zk: zk1:2181(CONNECTED) 19] get -s /temp
null                                    # 节点数据为空（null）
cZxid = 0x50000000b                     # 创建事务ID：0x50000000b (十六进制)
ctime = Fri Jan 02 06:27:27 UTC 2026    # 创建时间：2026年1月2日 06:27:27 UTC
mZxid = 0x50000000b                     # 修改事务ID：与 cZxid 相同，说明数据未被修改
mtime = Fri Jan 02 06:27:27 UTC 2026    # 修改时间：与创建时间相同
pZxid = 0x50000000c                     # 子节点变更事务ID：0x50000000c（比 cZxid 大1，说明创建了子节点）
cversion = 1                            # 子节点版本：1（有1次子节点变更）
dataVersion = 0                         # 数据版本：0（数据未被修改过）
aclVersion = 0                          # ACL版本：0（ACL未被修改过）
ephemeralOwner = 0x0                    # 临时节点所有者：0（表示这是持久节点）
dataLength = 0                          # 数据长度：0字节（节点数据为空）
numChildren = 1                         # 子节点数量：1个
```

**关键概念说明：**

1. **Zxid (ZooKeeper Transaction ID)**：
   - 全局递增的64位整数
   - 格式：`0x` + 十六进制数
   - 用于保证操作的全局顺序性
   - 每次写操作（create、set、delete）都会生成新的 Zxid

2. **版本号的作用（乐观锁）**：
   - `dataVersion`: 用于 `setData` 操作，防止并发修改冲突
   - `cversion`: 用于子节点操作，防止并发创建/删除冲突
   - `aclVersion`: 用于 ACL 操作，防止并发权限修改冲突
   - 示例：`set /test "data" 0` 中的 `0` 就是 dataVersion

3. **ephemeralOwner 判断节点类型**：
   - `0x0` (0): 持久节点（PERSISTENT）
   - 非零值: 临时节点（EPHEMERAL），值为创建该节点的会话ID

4. **pZxid 的作用**：
   - 跟踪子节点的创建和删除
   - 如果 `pZxid > cZxid`，说明创建节点后还创建了子节点
   - 示例中：`pZxid = 0x50000000c`，`cZxid = 0x50000000b`，说明创建了子节点

5. **版本号递增规则**：
   - 每次对应操作成功时递增
   - 初始值为 0
   - 用于实现乐观锁机制

### 3.4 节点修改（set）

```bash
# 修改节点数据
set /test "new data"

# 基于版本号修改（乐观锁）
set /test "new data" 0  # 0 是版本号，从 get 或 stat 命令获取

# 不指定版本号（可能覆盖并发修改）
set /test "new data" -1
```

### 3.5 节点删除（delete, deleteall）

```bash
# 删除节点（节点必须没有子节点）
delete /test

# 基于版本号删除（乐观锁）
delete /test 0  # 0 是版本号

# 递归删除节点及其所有子节点（3.5.0+）
deleteall /parent
```

### 3.6 批量操作（Multi/Transaction）

**注意**：批量操作功能仅在 ZooKeeper 3.5.0+ 版本中可用，且需要通过 Java API 使用，命令行客户端 `zkCli.sh` 不直接支持批量操作。

#### 3.6.1 批量操作概述

ZooKeeper 的 `multi` 操作允许在一个**事务**中执行多个操作，这些操作要么**全部成功**，要么**全部失败**（原子性）。

**特点**：
- ✅ **原子性**：所有操作作为一个事务执行
- ✅ **性能优化**：减少网络往返次数（N次操作 → 1次网络请求）
- ✅ **一致性**：保证操作的顺序性和一致性

#### 3.6.2 批量操作的优势

**性能对比**：

| 操作方式 | 网络请求次数 | 原子性 | 性能 |
|---------|------------|--------|------|
| **逐个操作** | N次 | ❌ | 慢 |
| **批量操作** | 1次 | ✅ | 快 |

**示例场景**：
- 批量创建节点：初始化时创建多个节点
- 批量获取数据：服务发现时获取所有实例数据
- 批量更新配置：同时更新多个配置项
- 批量删除节点：清理多个节点

#### 3.6.3 批量操作使用场景

**场景1：批量创建服务实例**

```java
// 创建多个服务实例节点
List<Op> ops = new ArrayList<>();
ops.add(Op.create("/services/user-service/instances/pod-001", 
        "10.244.1.1:8080".getBytes(), ZooDefs.Ids.OPEN_ACL_UNSAFE, 
        CreateMode.EPHEMERAL));
ops.add(Op.create("/services/user-service/instances/pod-002", 
        "10.244.1.2:8080".getBytes(), ZooDefs.Ids.OPEN_ACL_UNSAFE, 
        CreateMode.EPHEMERAL));
ops.add(Op.create("/services/user-service/instances/pod-003", 
        "10.244.1.3:8080".getBytes(), ZooDefs.Ids.OPEN_ACL_UNSAFE, 
        CreateMode.EPHEMERAL));

zk.multi(ops);  // 一次网络请求完成所有创建操作
```

**场景2：批量获取服务实例数据**

```java
// 获取所有服务实例的详细信息
List<String> instanceIds = zk.getChildren("/services/user-service/instances", null);

List<Op> ops = new ArrayList<>();
for (String id : instanceIds) {
    ops.add(Op.getData("/services/user-service/instances/" + id, false));
}

List<OpResult> results = zk.multi(ops);  // 一次网络请求获取所有数据
// 处理结果...
```

**场景3：批量更新配置（带版本检查）**

```java
// 同时更新多个配置项，使用版本号保证一致性
List<Op> ops = new ArrayList<>();
ops.add(Op.check("/config/app", 0));  // 检查版本号
ops.add(Op.setData("/config/app", "new config".getBytes(), 0));
ops.add(Op.check("/config/db", 1));
ops.add(Op.setData("/config/db", "new db config".getBytes(), 1));

zk.multi(ops);  // 如果版本号不匹配，整个事务回滚
```

#### 3.6.4 批量操作注意事项

1. **版本要求**：需要 ZooKeeper 3.5.0+ 版本
2. **原子性保证**：所有操作要么全部成功，要么全部失败
3. **顺序执行**：操作按照添加的顺序执行
4. **错误处理**：如果任何一个操作失败，整个事务回滚
5. **命令行限制**：`zkCli.sh` 不直接支持批量操作，需要通过 Java API

#### 3.6.5 批量操作 vs 逐个操作

**逐个操作示例**：
```java
// 需要 N 次网络请求
zk.create("/node1", "data1".getBytes(), ...);  // 请求1
zk.create("/node2", "data2".getBytes(), ...);  // 请求2
zk.create("/node3", "data3".getBytes(), ...);  // 请求3
// 如果第2个操作失败，第1个已经成功，数据不一致
```

**批量操作示例**：
```java
// 只需要 1 次网络请求
List<Op> ops = Arrays.asList(
    Op.create("/node1", "data1".getBytes(), ...),
    Op.create("/node2", "data2".getBytes(), ...),
    Op.create("/node3", "data3".getBytes(), ...)
);
zk.multi(ops);  // 如果第2个操作失败，所有操作都回滚，保证一致性
```

### 3.7 常见错误和解决方案

#### 错误1：Node does not exist（节点不存在）

**错误信息**：
```
Node does not exist: /level1/level2
```

**原因**：尝试创建多级路径时，父节点 `/level1` 不存在。

**解决方法**：
```bash
# 方法1：先创建父节点，再创建子节点
create /level1 ""
create /level1/level2 "hell"

# 方法2：创建父节点时也设置数据
create /level1 "parent data"
create /level1/level2 "hell"

# 方法3：使用 Java API 递归创建（需要自己实现）
# ZooKeeper 客户端不提供自动递归创建功能
```

#### 错误2：Node already exists（节点已存在）

**错误信息**：
```
Node already exists: /test
```

**解决方法**：
```bash
# 先检查节点是否存在
stat /test

# 如果存在，可以删除后重新创建
delete /test
create /test "new data"

# 或者直接修改现有节点
set /test "new data"
```

#### 错误3：Not empty（节点不为空）

**错误信息**：
```
Node not empty: /parent
```

**原因**：尝试删除包含子节点的节点。

**解决方法**：
```bash
# 方法1：先删除所有子节点，再删除父节点
delete /parent/child1
delete /parent/child2
delete /parent

# 方法2：使用 deleteall 命令（ZooKeeper 3.5.0+）
deleteall /parent
```

### 3.8 历史记录和命令补全

```bash
# 查看历史命令
history

# 执行历史命令
!1  # 执行第1条历史命令

# 命令补全（Tab键）
# 输入部分路径后按 Tab 键自动补全
```

---

## 4. 节点类型和特性

### 4.1 节点类型对比

| 类型 | 命令参数 | 特性 | 使用场景 |
|------|---------|------|----------|
| PERSISTENT | 无 | 持久存在，直到手动删除 | 配置信息、元数据 |
| EPHEMERAL | -e | 客户端断开自动删除 | 临时状态、服务发现 |
| PERSISTENT_SEQUENTIAL | -s | 持久 + 自动序号 | 任务队列、有序ID |
| EPHEMERAL_SEQUENTIAL | -e -s | 临时 + 自动序号 | 分布式锁、临时任务 |

### 4.2 实际应用示例

#### 服务注册与发现
```bash
# 服务注册（临时节点）
create -e /services/service1 "192.168.1.100:8080"

# 服务发现（列出所有服务）
ls /services
```

#### 分布式锁
```bash
# 创建锁节点（临时顺序节点）
create -e -s /locks/resource ""

# 获取所有锁节点，判断自己是否是最小的序号
ls /locks/resource
```

#### 配置管理
```bash
# 创建配置节点（持久节点）
create /config/app "{\"timeout\":30,\"retry\":3}"

# 读取配置
get /config/app
```

---

## 5. Watch 机制

### 5.1 Watch 类型

ZooKeeper 的 Watch 是一次性的，触发后需要重新注册。

#### 节点数据变化 Watch
```bash
# 注册数据变化监听
get /test watch

# 在另一个客户端修改数据
set /test "changed data"

# 原客户端会收到 NodeDataChanged 事件
```

#### 子节点变化 Watch
```bash
# 注册子节点变化监听
ls /parent watch

# 在另一个客户端创建子节点
create /parent/child "data"

# 原客户端会收到 NodeChildrenChanged 事件
```

### 5.2 Watch 事件类型

- `NodeCreated`: 节点被创建
- `NodeDeleted`: 节点被删除
- `NodeDataChanged`: 节点数据被修改
- `NodeChildrenChanged`: 子节点列表发生变化

### 5.3 Java API 中使用 Watch

```java
// 方式1：使用 Watcher 接口
zk.getData("/test", new Watcher() {
    @Override
    public void process(WatchedEvent event) {
        System.out.println("事件类型: " + event.getType());
        System.out.println("事件路径: " + event.getPath());
    }
}, null);

// 方式2：使用 boolean 参数（使用默认 Watcher）
zk.getData("/test", true, null);

// 方式3：使用异步回调
zk.getData("/test", true, new AsyncCallback.DataCallback() {
    @Override
    public void processResult(int rc, String path, Object ctx, byte[] data, Stat stat) {
        // 处理结果
    }
}, null);
```

---

## 6. ACL 权限控制

### 6.1 ACL 组成

ACL (Access Control List) 由三部分组成：
- **Scheme**: 权限模式（world, ip, digest, auth）
- **ID**: 授权对象
- **Permission**: 权限（READ, WRITE, CREATE, DELETE, ADMIN）

### 6.2 权限类型

- `r` (READ): 读取节点数据和子节点列表
- `w` (WRITE): 修改节点数据
- `c` (CREATE): 创建子节点
- `d` (DELETE): 删除子节点
- `a` (ADMIN): 设置 ACL 权限

### 6.3 ACL 命令示例

```bash
# 查看节点 ACL
getAcl /test

# 设置 ACL（world 模式，所有人可读）
setAcl /test world:anyone:r

# 设置 ACL（IP 模式）
setAcl /test ip:192.168.1.100:rwcda

# 设置 ACL（digest 模式，用户名密码）
# 先创建用户
addauth digest user1:password1
setAcl /test digest:user1:password1:rwcda

# 设置 ACL（auth 模式，当前认证用户）
addauth digest user1:password1
setAcl /test auth:user1:rwcda
```

### 6.4 默认 ACL

```bash
# 创建节点时指定 ACL
create /test "data" world:anyone:cdrwa

# 使用系统默认 ACL（OPEN_ACL_UNSAFE）
create /test "data" world:anyone:cdrwa
```

---

## 7. 集群管理命令

### 7.1 查看节点角色（Leader/Follower）

#### 方法1：使用 zkServer.sh status（推荐）
```bash
# 查询 zk1 节点角色
docker exec zk1-3.4.6 zkServer.sh status

# 查询 zk2 节点角色
docker exec zk2-3.4.6 zkServer.sh status

# 查询 zk3 节点角色
docker exec zk3-3.4.6 zkServer.sh status

# 输出示例：
# ZooKeeper JMX enabled by default
# Using config: /conf/zoo.cfg
# Client port found: 2181. Client address: localhost. Client SSL: false.
# Mode: follower  # 或 leader
```

#### 方法2：使用四字命令 stat
```bash
# 从容器内执行
docker exec zk1-3.4.6 sh -c "echo stat | nc localhost 2181"

# 从宿主机执行（需要本地有 nc 命令）
echo stat | nc localhost 2181

# 输出中包含 Mode 信息：
# Mode: follower 或 Mode: leader
```

#### 方法3：使用四字命令 mntr（最详细）
```bash
# 查询节点详细状态
docker exec zk1-3.4.6 sh -c "echo mntr | nc localhost 2181"

# 关键字段：
# zk_server_state=leader 或 zk_server_state=follower
# zk_version=版本号
# zk_avg_latency=平均延迟
# zk_max_latency=最大延迟
# zk_min_latency=最小延迟
# zk_packets_received=接收的包数
# zk_packets_sent=发送的包数
# zk_num_alive_connections=活跃连接数
# zk_outstanding_requests=待处理请求数
# zk_znode_count=节点总数
# zk_watch_count=Watch 总数
```

#### 方法4：查看日志
```bash
# 查看节点日志，搜索 Leader 或 Follower 关键字
docker logs zk1-3.4.6 2>&1 | grep -i "leader\|follower"

# Leader 节点日志示例：
# INFO [QuorumPeer...Leader@xxx] - ...

# Follower 节点日志示例：
# INFO [QuorumPeer...Follower@xxx] - ...
# INFO [QuorumPeer...] - Peer state changed: following - broadcast
```

### 7.2 节点角色说明

| 角色 | 说明 | 特点 |
|------|------|------|
| **Leader** | 集群主节点 | - 处理所有写请求<br>- 负责事务提案和提交<br>- 集群中只有一个 Leader |
| **Follower** | 集群从节点 | - 处理读请求<br>- 参与 Leader 选举<br>- 同步 Leader 的数据<br>- 可以参与写请求的投票 |
| **Observer** | 观察者节点 | - 处理读请求<br>- 不参与选举和投票<br>- 只同步数据<br>- 用于扩展读性能 |

**当前集群状态：**
- zk1: **Follower**
- zk2: **Follower**
- zk3: **Leader**

### 7.3 四字命令（4LW Commands）详解

四字命令是 ZooKeeper 提供的管理命令，通过向客户端端口发送 4 个字母的命令来获取信息。

#### 7.3.1 基本健康检查命令

```bash
# ruok: 检查服务器是否运行正常（Are You OK?）
docker exec zk1-3.4.6 sh -c "echo ruok | nc localhost 2181"
# 返回: imok（表示服务器正常）

# conf: 查看服务器配置信息
docker exec zk1-3.4.6 sh -c "echo conf | nc localhost 2181"
# 输出包含：clientPort, dataDir, dataLogDir, tickTime 等配置

# stat: 查看服务器状态和客户端连接信息
docker exec zk1-3.4.6 sh -c "echo stat | nc localhost 2181"
# 输出包含：
# - ZooKeeper version（版本信息）
# - Latency min/avg/max（延迟统计）
# - Received/Sent（收发统计）
# - Connections（连接数）
# - Mode（节点角色：leader/follower）
# - Node count（节点总数）
```

#### 7.3.2 监控和性能命令

```bash
# mntr: 监控服务器健康状态（Monitor）
docker exec zk1-3.4.6 sh -c "echo mntr | nc localhost 2181"
# 输出关键指标：
# zk_version=3.6.3-...
# zk_server_state=leader/follower
# zk_avg_latency=0
# zk_max_latency=0
# zk_min_latency=0
# zk_packets_received=1234
# zk_packets_sent=1234
# zk_num_alive_connections=5
# zk_outstanding_requests=0
# zk_znode_count=10
# zk_watch_count=5
# zk_ephemerals_count=2
# zk_approximate_data_size=1024

# dump: 列出未完成的会话和临时节点
docker exec zk1-3.4.6 sh -c "echo dump | nc localhost 2181"
# 输出所有会话和临时节点信息

# envi: 查看服务器环境信息（Environment）
docker exec zk1-3.4.6 sh -c "echo envi | nc localhost 2181"
# 输出 Java 环境变量、系统属性等
```

#### 7.3.3 Watch 相关命令

```bash
# wchs: 查看 Watch 摘要信息（Watch Summary）
docker exec zk1-3.4.6 sh -c "echo wchs | nc localhost 2181"
# 输出：Watch 总数、连接数等摘要信息

# wchc: 按会话列出 Watch 信息（Watch by Connection）
docker exec zk1-3.4.6 sh -c "echo wchc | nc localhost 2181"
# 输出：每个会话 ID 对应的 Watch 路径列表
# 注意：需要启用 4LW 命令白名单

# wchp: 按路径列出 Watch 信息（Watch by Path）
docker exec zk1-3.4.6 sh -c "echo wchp | nc localhost 2181"
# 输出：每个路径对应的会话 ID 列表
# 注意：需要启用 4LW 命令白名单
```

#### 7.3.4 从宿主机执行四字命令

如果本地安装了 `nc`（netcat）命令，可以直接从宿主机执行：

```bash
# 检查 zk1 节点健康
echo ruok | nc localhost 2181

# 查看 zk1 节点状态
echo stat | nc localhost 2181

# 查看 zk2 节点状态
echo stat | nc localhost 2182

# 查看 zk3 节点状态
echo stat | nc localhost 2183
```

### 7.4 集群健康检查脚本

创建一个快速检查所有节点状态的脚本：

```bash
#!/bin/bash
# check-all-nodes.sh

echo "=== ZooKeeper 集群节点状态检查 ==="
echo ""

for i in 1 2 3; do
    container="zk${i}-3.4.6"
    port=$((2180 + i))
    
    echo "--- 节点 zk${i} (端口 ${port}) ---"
    
    # 检查健康状态
    health=$(docker exec $container sh -c "echo ruok | nc localhost 2181" 2>/dev/null)
    if [ "$health" = "imok" ]; then
        echo "✓ 健康状态: 正常"
    else
        echo "✗ 健康状态: 异常"
    fi
    
    # 检查节点角色
    mode=$(docker exec $container sh -c "echo stat | nc localhost 2181" 2>/dev/null | grep "Mode:")
    echo "  角色: $mode"
    
    # 获取连接数
    connections=$(docker exec $container sh -c "echo stat | nc localhost 2181" 2>/dev/null | grep "Connections:")
    echo "  $connections"
    
    echo ""
done
```

### 7.5 集群配置查询

```bash
# 查看集群配置（在 zkCli.sh 中执行）
docker exec -it zk1-3.4.6 zkCli.sh -server localhost:2181

# 在客户端中执行：
get /zookeeper/config
# 返回集群配置信息

# 查看集群成员
get /zookeeper/config | grep server
```

### 7.6 常用集群管理操作

```bash
# 1. 查看所有容器状态
docker ps --filter "name=zk"

# 2. 查看容器日志（实时）
docker logs -f zk1-3.4.6

# 3. 重启单个节点
docker restart zk1-3.4.6

# 4. 停止整个集群
docker-compose -f docker-compose-zk346.yml down

# 5. 启动整个集群
docker-compose -f docker-compose-zk346.yml up -d

# 6. 查看集群网络
docker network inspect zookeeper-study_zk346-net

# 7. 进入容器内部
docker exec -it zk1-3.4.6 bash
```

### 7.7 动态配置（3.7.0+）

**注意**：动态配置功能仅在 ZooKeeper 3.7.0+ 版本中可用，且需要启用 `reconfigEnabled=true`。

```bash
# 连接到支持动态配置的集群
docker exec -it zk1-3.7.0-dynamic zkCli.sh -server zk1:2181

# 在客户端中执行以下命令：

# 查看当前配置
reconfig -display

# 添加新节点
reconfig -add server.4=zk4:2888:3888:participant;2181

# 移除节点
reconfig -remove 4

# 设置节点为观察者模式
reconfig -add server.4=zk4:2888:3888:observer;2181

# 查看配置变更历史
get /zookeeper/config
```

### 7.8 故障排查命令

```bash
# 1. 检查节点是否正常启动
docker exec zk1-3.4.6 sh -c "echo ruok | nc localhost 2181"
# 应该返回: imok

# 2. 检查端口是否监听
docker exec zk1-3.4.6 sh -c "netstat -tln | grep 2181" || echo "使用其他方法检查"

# 3. 查看错误日志
docker logs zk1-3.4.6 2>&1 | grep -i error

# 4. 检查集群选举状态
docker logs zk1-3.4.6 2>&1 | grep -i "election\|leader\|follower"

# 5. 检查数据目录
docker exec zk1-3.4.6 ls -la /data/version-2/
docker exec zk1-3.4.6 ls -la /datalog/version-2/

# 6. 检查 myid 文件
docker exec zk1-3.4.6 cat /data/myid
# 应该返回: 1（对应 ZOO_MY_ID）
```

---

## 8. Java API 示例

### 8.1 基本连接和操作

```java
import org.apache.zookeeper.*;
import org.apache.zookeeper.data.Stat;
import java.util.concurrent.CountDownLatch;

public class ZKExample {
    private static ZooKeeper zk;
    private static CountDownLatch connectedSemaphore = new CountDownLatch(1);
    
    public static void main(String[] args) throws Exception {
        // 连接 ZooKeeper
        zk = new ZooKeeper("192.168.160.11:2181,192.168.160.12:2181,192.168.160.13:2181",
                3000, new Watcher() {
            @Override
            public void process(WatchedEvent event) {
                if (event.getState() == Event.KeeperState.SyncConnected) {
                    connectedSemaphore.countDown();
                }
            }
        });
        
        // 等待连接建立
        connectedSemaphore.await();
        System.out.println("ZooKeeper 连接成功！");
        
        // 创建节点
        String path = zk.create("/test", "data".getBytes(),
                ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.PERSISTENT);
        System.out.println("创建节点: " + path);
        
        // 读取节点
        byte[] data = zk.getData("/test", false, null);
        System.out.println("节点数据: " + new String(data));
        
        // 修改节点
        Stat stat = zk.setData("/test", "new data".getBytes(), -1);
        System.out.println("修改成功，版本号: " + stat.getVersion());
        
        // 列出子节点
        java.util.List<String> children = zk.getChildren("/", false);
        System.out.println("根节点子节点: " + children);
        
        // 删除节点
        zk.delete("/test", -1);
        System.out.println("节点已删除");
        
        // 关闭连接
        zk.close();
    }
}
```

### 8.2 Watch 使用示例

```java
// 注册 Watch 监听节点数据变化
zk.getData("/test", new Watcher() {
    @Override
    public void process(WatchedEvent event) {
        if (event.getType() == Event.EventType.NodeDataChanged) {
            try {
                // 重新获取数据并重新注册 Watch
                byte[] data = zk.getData("/test", this, null);
                System.out.println("数据已更新: " + new String(data));
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }
}, null);
```

### 8.3 异步操作示例

```java
// 异步创建节点
zk.create("/async-node", "data".getBytes(),
        ZooDefs.Ids.OPEN_ACL_UNSAFE,
        CreateMode.PERSISTENT,
        new AsyncCallback.StringCallback() {
            @Override
            public void processResult(int rc, String path, Object ctx, String name) {
                if (rc == KeeperException.Code.OK.intValue()) {
                    System.out.println("异步创建成功: " + name);
                }
            }
        }, "context");
```

### 8.4 批量操作（Multi/Transaction）

**注意**：批量操作功能仅在 ZooKeeper 3.5.0+ 版本中可用。

#### 8.4.1 批量操作概述

ZooKeeper 的 `multi` 操作允许在一个事务中执行多个操作，这些操作要么**全部成功**，要么**全部失败**（原子性）。

**特点**：
- ✅ **原子性**：所有操作作为一个事务执行
- ✅ **性能优化**：减少网络往返次数
- ✅ **一致性**：保证操作的顺序性

#### 8.4.2 批量操作支持的操作类型

- `Op.create()`: 创建节点
- `Op.delete()`: 删除节点
- `Op.setData()`: 修改节点数据
- `Op.check()`: 检查节点版本（用于乐观锁）
- `Op.getData()`: 获取节点数据（只读操作）

#### 8.4.3 Java API 批量操作示例

**示例1：批量创建节点**

```java
import org.apache.zookeeper.*;
import org.apache.zookeeper.data.ACL;
import java.util.*;

// 批量创建多个节点
List<Op> ops = new ArrayList<>();
ops.add(Op.create("/batch/node1", "data1".getBytes(), 
        ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.PERSISTENT));
ops.add(Op.create("/batch/node2", "data2".getBytes(), 
        ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.PERSISTENT));
ops.add(Op.create("/batch/node3", "data3".getBytes(), 
        ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.PERSISTENT));

try {
    // 批量执行，要么全部成功，要么全部失败
    List<OpResult> results = zk.multi(ops);
    
    // 处理结果
    for (OpResult result : results) {
        if (result instanceof OpResult.CreateResult) {
            OpResult.CreateResult createResult = (OpResult.CreateResult) result;
            System.out.println("创建成功: " + createResult.getPath());
        }
    }
} catch (KeeperException e) {
    // 如果任何一个操作失败，整个事务回滚
    System.err.println("批量操作失败: " + e.getMessage());
}
```

**示例2：批量获取节点数据**

```java
// 批量获取多个节点的数据
List<String> paths = Arrays.asList(
    "/x-system/services/x-user-service/instances/pod-001",
    "/x-system/services/x-user-service/instances/pod-002",
    "/x-system/services/x-user-service/instances/pod-003"
);

List<Op> ops = new ArrayList<>();
for (String path : paths) {
    ops.add(Op.getData(path, false));
}

try {
    List<OpResult> results = zk.multi(ops);
    
    List<String> instanceData = new ArrayList<>();
    for (OpResult result : results) {
        if (result instanceof OpResult.GetDataResult) {
            OpResult.GetDataResult getDataResult = (OpResult.GetDataResult) result;
            byte[] data = getDataResult.getData();
            instanceData.add(new String(data));
        }
    }
    
    System.out.println("批量获取成功，共 " + instanceData.size() + " 个实例");
} catch (KeeperException e) {
    System.err.println("批量获取失败: " + e.getMessage());
}
```

**示例3：批量更新节点（带版本检查）**

```java
// 批量更新多个节点，使用版本号保证一致性
List<Op> ops = new ArrayList<>();

// 先检查版本号（乐观锁）
ops.add(Op.check("/config/app", 0));  // 检查版本号是否为0
ops.add(Op.setData("/config/app", "new config".getBytes(), 0));

ops.add(Op.check("/config/db", 1));   // 检查版本号是否为1
ops.add(Op.setData("/config/db", "new db config".getBytes(), 1));

try {
    List<OpResult> results = zk.multi(ops);
    System.out.println("批量更新成功");
} catch (KeeperException.BadVersionException e) {
    // 版本号不匹配，整个事务回滚
    System.err.println("版本号不匹配，更新失败");
}
```

**示例4：批量删除节点**

```java
// 批量删除多个节点
List<Op> ops = new ArrayList<>();
ops.add(Op.delete("/batch/node1", -1));
ops.add(Op.delete("/batch/node2", -1));
ops.add(Op.delete("/batch/node3", -1));

try {
    List<OpResult> results = zk.multi(ops);
    System.out.println("批量删除成功");
} catch (KeeperException e) {
    System.err.println("批量删除失败: " + e.getMessage());
}
```

**示例5：混合操作（创建、更新、删除）**

```java
// 在一个事务中执行不同类型的操作
List<Op> ops = new ArrayList<>();

// 创建新节点
ops.add(Op.create("/batch/new-node", "new data".getBytes(), 
        ZooDefs.Ids.OPEN_ACL_UNSAFE, CreateMode.PERSISTENT));

// 更新现有节点
ops.add(Op.setData("/batch/existing-node", "updated data".getBytes(), -1));

// 删除节点
ops.add(Op.delete("/batch/old-node", -1));

try {
    List<OpResult> results = zk.multi(ops);
    System.out.println("混合操作成功");
} catch (KeeperException e) {
    // 如果任何一个操作失败，所有操作都会回滚
    System.err.println("混合操作失败: " + e.getMessage());
}
```

#### 8.4.4 批量操作的优势

| 特性 | 逐个操作 | 批量操作 |
|------|---------|---------|
| **网络请求** | N次 | 1次 |
| **原子性** | ❌ | ✅ |
| **性能** | 慢 | 快 |
| **一致性** | 可能不一致 | 保证一致 |

#### 8.4.5 批量操作注意事项

1. **版本要求**：需要 ZooKeeper 3.5.0+ 版本
2. **原子性**：所有操作要么全部成功，要么全部失败
3. **顺序性**：操作按照添加的顺序执行
4. **错误处理**：如果任何一个操作失败，整个事务回滚
5. **性能**：批量操作可以显著减少网络往返次数

#### 8.4.6 批量操作最佳实践

1. **批量创建**：初始化时批量创建多个节点
2. **批量获取**：服务发现时批量获取所有实例数据
3. **批量更新**：配置变更时批量更新多个配置项
4. **版本检查**：使用 `Op.check()` 实现乐观锁

**示例：服务发现批量获取优化**

```java
// 优化前：逐个获取（N+1次网络请求）
List<String> instanceIds = zk.getChildren("/services/x-user-service/instances", null);
for (String id : instanceIds) {
    byte[] data = zk.getData("/services/x-user-service/instances/" + id, false, null);
    // 处理数据
}

// 优化后：批量获取（2次网络请求）
List<String> instanceIds = zk.getChildren("/services/x-user-service/instances", null);
List<Op> ops = new ArrayList<>();
for (String id : instanceIds) {
    ops.add(Op.getData("/services/x-user-service/instances/" + id, false));
}
List<OpResult> results = zk.multi(ops);
// 处理结果
```

---

## 9. 常见使用场景

### 9.1 配置中心

```bash
# 创建配置节点
create /config/app/database "jdbc:mysql://localhost:3306/db"

# 应用监听配置变化
# Java 代码中使用 Watch 监听 /config/app/database
```

### 9.2 服务注册与发现

```bash
# 服务注册（临时节点）
create -e /services/user-service "192.168.1.100:8080"

# 服务发现
ls /services
get /services/user-service
```

### 9.3 分布式锁

```bash
# 创建锁节点（临时顺序节点）
create -e -s /locks/resource ""

# 获取所有锁节点，判断序号最小的获得锁
ls /locks/resource
```

### 9.4 分布式队列

```bash
# 创建队列节点（顺序节点）
create -s /queue/task "task-data"

# 消费队列（按序号顺序处理）
ls /queue
get /queue/task0000000001
```

### 9.5 集群选主（Leader Election）

```bash
# 每个节点创建临时顺序节点
create -e -s /election/leader ""

# 序号最小的节点成为 Leader
# 其他节点监听前一个节点的删除事件
```

---

## 10. 故障排查

### 10.1 连接问题

```bash
# 检查端口是否开放
netstat -an | grep 2181

# 检查防火墙
# macOS/Linux
sudo lsof -i :2181

# 测试连接
telnet localhost 2181
```

### 10.2 查看日志

```bash
# 查看容器日志
docker logs zk1-3.4.6

# 实时查看日志
docker logs -f zk1-3.4.6
```

### 10.3 常见错误

- **ConnectionLoss**: 连接丢失，需要重试
- **SessionExpired**: 会话过期，需要重新连接
- **NodeExists**: 节点已存在
- **NoNode**: 节点不存在
- **BadVersion**: 版本号不匹配（并发修改）

---

## 11. 最佳实践

1. **连接管理**: 使用连接池或单例模式管理 ZooKeeper 连接
2. **异常处理**: 正确处理 ConnectionLoss 和 SessionExpired 异常
3. **Watch 重注册**: Watch 是一次性的，触发后需要重新注册
4. **版本控制**: 使用版本号实现乐观锁，避免并发修改冲突
5. **节点设计**: 
   - 临时节点用于服务注册
   - 顺序节点用于队列和锁
   - 持久节点用于配置和元数据
6. **ACL 安全**: 生产环境使用 ACL 控制访问权限
7. **监控告警**: 监控集群状态和性能指标

---

## 12. 学习资源

- **官方文档**: https://zookeeper.apache.org/doc/
- **Java API**: https://zookeeper.apache.org/doc/current/api/index.html
- **命令行工具**: `zkCli.sh` 内置帮助命令 `help`

---

**提示**: 建议在学习过程中：
1. 先熟悉基本命令（create, get, set, delete, ls）
2. 理解节点类型和特性
3. 掌握 Watch 机制
4. 学习 Java API 使用
5. 实践常见分布式场景

祝学习愉快！🎉

