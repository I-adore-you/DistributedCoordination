# Apache Curator 功能详解

Apache Curator 是一个用于简化 Apache ZooKeeper 使用的 Java 客户端库。它不仅提供了分布式锁，还封装了许多常见的分布式系统模式和工具。

---

## 目录

1. [Curator 概述](#1-curator-概述)
2. [核心模块](#2-核心模块)
3. [分布式锁（Distributed Lock）](#3-分布式锁distributed-lock)
4. [领导者选举（Leader Election）](#4-领导者选举leader-election)
5. [分布式队列（Distributed Queue）](#5-分布式队列distributed-queue)
6. [分布式计数器（Distributed Counter）](#6-分布式计数器distributed-counter)
7. [服务发现（Service Discovery）](#7-服务发现service-discovery)
8. [缓存（Cache）](#8-缓存cache)
9. [信号量（Semaphore）](#9-信号量semaphore)
10. [栅栏（Barrier）](#10-栅栏barrier)
11. [分布式原子值（Atomic Value）](#11-分布式原子值atomic-value)
12. [节点监听（Node Watcher）](#12-节点监听node-watcher)
13. [事务支持（Transaction）](#13-事务支持transaction)
14. [测试工具（Testing）](#14-测试工具testing)
15. [功能对比总结](#15-功能对比总结)

---

## 1. Curator 概述

### 1.1 什么是 Apache Curator？

Apache Curator 是 Netflix 开源的一个 ZooKeeper 客户端库，后来捐赠给 Apache 基金会。它提供了：

- **高级 API**：简化 ZooKeeper 的使用
- **常用模式**：封装了分布式系统中的常见模式
- **可靠性**：自动处理连接、重试、故障恢复
- **易用性**：提供简洁的 API，降低学习成本

### 1.2 Curator 模块结构

```
curator-framework      # 核心框架，提供高级 API
curator-recipes        # 常用模式实现（锁、选举、队列等）
curator-client         # 底层客户端封装
curator-x-discovery    # 服务发现
curator-x-async        # 异步 API
curator-test           # 测试工具
```

### 1.3 Maven 依赖

```xml
<!-- 核心框架 -->
<dependency>
    <groupId>org.apache.curator</groupId>
    <artifactId>curator-framework</artifactId>
    <version>5.5.0</version>
</dependency>

<!-- 常用模式（包含所有 Recipes） -->
<dependency>
    <groupId>org.apache.curator</groupId>
    <artifactId>curator-recipes</artifactId>
    <version>5.5.0</version>
</dependency>

<!-- 服务发现（可选） -->
<dependency>
    <groupId>org.apache.curator</groupId>
    <artifactId>curator-x-discovery</artifactId>
    <version>5.5.0</version>
</dependency>

<!-- 测试工具（可选） -->
<dependency>
    <groupId>org.apache.curator</groupId>
    <artifactId>curator-test</artifactId>
    <version>5.5.0</version>
</dependency>
```

---

## 2. 核心模块

### 2.1 Curator Framework

**用途**：提供高级 API，简化 ZooKeeper 操作

**核心功能**：
- 连接管理
- 自动重试机制
- 会话管理
- 节点操作封装

**示例**：

```java
CuratorFramework client = CuratorFrameworkFactory.builder()
    .connectString("127.0.0.1:2181")
    .sessionTimeoutMs(5000)
    .connectionTimeoutMs(3000)
    .retryPolicy(new ExponentialBackoffRetry(1000, 3))
    .build();

client.start();

// 创建节点
client.create()
    .creatingParentContainersIfNeeded()
    .withMode(CreateMode.PERSISTENT)
    .forPath("/path/to/node", "data".getBytes());

// 读取节点
byte[] data = client.getData().forPath("/path/to/node");

// 更新节点
client.setData().forPath("/path/to/node", "new data".getBytes());

// 删除节点
client.delete().forPath("/path/to/node");
```

### 2.2 Curator Recipes

**用途**：提供常见的分布式系统模式实现

**包含的模式**：
- 分布式锁
- 领导者选举
- 分布式队列
- 分布式计数器
- 信号量
- 栅栏
- 分布式原子值
- 等等...

---

## 3. 分布式锁（Distributed Lock）

### 3.1 功能说明

**用途**：确保在分布式环境中对共享资源的互斥访问

**实现方式**：基于 ZooKeeper 临时顺序节点

### 3.2 锁类型

#### 3.2.1 可重入锁（InterProcessMutex）

**用途**：同一线程可以多次获取同一把锁

**示例**：

```java
InterProcessMutex lock = new InterProcessMutex(client, "/locks/myLock");

try {
    lock.acquire();
    // 执行业务逻辑
    doSomething();
} finally {
    lock.release();
}
```

#### 3.2.2 读写锁（InterProcessReadWriteLock）

**用途**：支持多个读锁或一个写锁

**示例**：

```java
InterProcessReadWriteLock rwLock = new InterProcessReadWriteLock(
    client, "/locks/myRWLock");

// 读锁
InterProcessMutex readLock = rwLock.readLock();
readLock.acquire();
try {
    // 读取操作
    readData();
} finally {
    readLock.release();
}

// 写锁
InterProcessMutex writeLock = rwLock.writeLock();
writeLock.acquire();
try {
    // 写入操作
    writeData();
} finally {
    writeLock.release();
}
```

#### 3.2.3 信号量锁（InterProcessSemaphoreV2）

**用途**：控制同时访问资源的线程数量

**示例**：

```java
InterProcessSemaphoreV2 semaphore = new InterProcessSemaphoreV2(
    client, "/semaphores/mySemaphore", 10); // 最多10个许可

Lease lease = semaphore.acquire();
try {
    // 执行业务逻辑（最多10个线程同时执行）
    doSomething();
} finally {
    semaphore.returnLease(lease);
}
```

#### 3.2.4 多锁（InterProcessMultiLock）

**用途**：同时获取多个锁，全部成功才算成功

**示例**：

```java
InterProcessMutex lock1 = new InterProcessMutex(client, "/locks/lock1");
InterProcessMutex lock2 = new InterProcessMutex(client, "/locks/lock2");
InterProcessMutex lock3 = new InterProcessMutex(client, "/locks/lock3");

InterProcessMultiLock multiLock = new InterProcessMultiLock(
    Arrays.asList(lock1, lock2, lock3));

try {
    multiLock.acquire();
    // 所有锁都获取成功，执行业务逻辑
    doSomething();
} finally {
    multiLock.release();
}
```

### 3.3 使用场景

- ✅ 防止重复提交
- ✅ 分布式任务调度
- ✅ 缓存更新锁
- ✅ 资源互斥访问

---

## 4. 领导者选举（Leader Election）

### 4.1 功能说明

**用途**：在集群中选举出一个主节点，负责特定任务的执行

**实现方式**：基于 ZooKeeper 临时顺序节点，最小序号成为 Leader

### 4.2 实现方式

#### 4.2.1 LeaderSelector（推荐）

**特点**：
- 自动重新选举
- 支持 Leader 回调
- 支持 Leader 放弃

**示例**：

```java
LeaderSelector leaderSelector = new LeaderSelector(
    client, "/election/myLeader", new LeaderSelectorListener() {
        @Override
        public void takeLeadership(CuratorFramework client) throws Exception {
            // 成为 Leader 后执行的逻辑
            System.out.println("I am the leader!");
            
            // 执行业务逻辑
            doLeaderWork();
            
            // 注意：方法返回时，会自动放弃 Leader 身份
        }
        
        @Override
        public void stateChanged(CuratorFramework client, ConnectionState newState) {
            // 连接状态变化时的处理
        }
    });

// 自动重新选举
leaderSelector.autoRequeue();
leaderSelector.start();

// 关闭
leaderSelector.close();
```

#### 4.2.2 LeaderLatch

**特点**：
- 简单的 Leader 选举
- 需要手动检查是否成为 Leader
- 不支持自动重新选举

**示例**：

```java
LeaderLatch leaderLatch = new LeaderLatch(client, "/election/myLeader");
leaderLatch.start();

try {
    // 等待成为 Leader（最多等待10秒）
    boolean isLeader = leaderLatch.await(10, TimeUnit.SECONDS);
    
    if (isLeader) {
        System.out.println("I am the leader!");
        // 执行业务逻辑
        doLeaderWork();
    }
} finally {
    leaderLatch.close();
}
```

### 4.3 使用场景

- ✅ 主从架构（Master-Slave）
- ✅ 定时任务调度（确保只有一个节点执行）
- ✅ 配置管理（主节点负责更新配置）
- ✅ 分布式协调（选举协调者）

---

## 5. 分布式队列（Distributed Queue）

### 5.1 功能说明

**用途**：实现跨节点的任务队列，支持任务的有序处理

**实现方式**：基于 ZooKeeper 顺序节点

### 5.2 队列类型

#### 5.2.1 简单队列（DistributedQueue）

**特点**：
- FIFO（先进先出）
- 支持优先级
- 支持阻塞和非阻塞操作

**示例**：

```java
// 生产者
DistributedQueue<String> queue = QueueBuilder.builder(
    client, new QueueConsumer<String>() {
        @Override
        public void consumeMessage(String message) throws Exception {
            // 消费消息
            System.out.println("Consumed: " + message);
        }
        
        @Override
        public void stateChanged(CuratorFramework client, ConnectionState newState) {
            // 连接状态变化
        }
    }, new QueueSerializer<String>() {
        @Override
        public byte[] serialize(String item) {
            return item.getBytes();
        }
        
        @Override
        public String deserialize(byte[] bytes) {
            return new String(bytes);
        }
    }, "/queues/myQueue").buildQueue();

queue.start();

// 生产消息
queue.put("message1");
queue.put("message2");
```

#### 5.2.2 优先级队列（DistributedPriorityQueue）

**特点**：
- 支持优先级排序
- FIFO 基础上增加优先级

**示例**：

```java
DistributedPriorityQueue<String> priorityQueue = QueueBuilder.builder(
    client, consumer, serializer, "/queues/myPriorityQueue")
    .buildPriorityQueue(0); // 0 表示无优先级限制

priorityQueue.start();

// 生产消息（带优先级）
priorityQueue.put("message1", 10); // 优先级 10
priorityQueue.put("message2", 5);  // 优先级 5（先处理）
```

#### 5.2.3 延迟队列（DistributedDelayQueue）

**特点**：
- 支持延迟消费
- 消息在指定时间后才可消费

**示例**：

```java
DistributedDelayQueue<String> delayQueue = QueueBuilder.builder(
    client, consumer, serializer, "/queues/myDelayQueue")
    .buildDelayQueue();

delayQueue.start();

// 生产消息（延迟5秒）
delayQueue.put("message1", System.currentTimeMillis() + 5000);
```

### 5.3 使用场景

- ✅ 分布式任务调度
- ✅ 消息队列
- ✅ 任务分发
- ✅ 异步处理

---

## 6. 分布式计数器（Distributed Counter）

### 6.1 功能说明

**用途**：提供跨节点的计数功能，适用于统计和限流等场景

**实现方式**：基于 ZooKeeper 节点存储计数值

### 6.2 计数器类型

#### 6.2.1 共享计数器（SharedCount）

**特点**：
- 多个客户端共享同一个计数器
- 支持原子操作
- 支持监听变化

**示例**：

```java
SharedCount sharedCount = new SharedCount(client, "/counters/myCounter", 0);
sharedCount.start();

// 监听变化
sharedCount.addListener(new SharedCountListener() {
    @Override
    public void countHasChanged(SharedCountReader sharedCount, int newCount) throws Exception {
        System.out.println("Counter changed to: " + newCount);
    }
    
    @Override
    public void stateChanged(CuratorFramework client, ConnectionState newState) {
        // 连接状态变化
    }
});

// 增加计数
sharedCount.setCount(sharedCount.getCount() + 1);

// 或者使用 trySetCount（原子操作）
boolean success = sharedCount.trySetCount(sharedCount.getVersionedValue(), 10);
```

#### 6.2.2 分布式长整型计数器（DistributedAtomicLong）

**特点**：
- 支持长整型
- 原子操作
- 支持 CAS（Compare-And-Swap）

**示例**：

```java
DistributedAtomicLong atomicLong = new DistributedAtomicLong(
    client, "/counters/myAtomicLong", new RetryNTimes(3, 1000));

// 增加并获取新值
AtomicValue<Long> result = atomicLong.add(1L);
if (result.succeeded()) {
    System.out.println("New value: " + result.postValue());
}

// CAS 操作
AtomicValue<Long> casResult = atomicLong.compareAndSet(10L, 20L);
if (casResult.succeeded()) {
    System.out.println("CAS succeeded");
}
```

### 6.3 使用场景

- ✅ 访问量统计
- ✅ 限流（令牌桶、漏桶）
- ✅ 分布式 ID 生成
- ✅ 计数器服务

---

## 7. 服务发现（Service Discovery）

### 7.1 功能说明

**用途**：帮助应用程序在分布式环境中注册和发现服务

**实现方式**：基于 ZooKeeper 节点存储服务信息

### 7.2 使用示例

```java
// 服务实例信息
ServiceInstance<InstanceDetails> instance = ServiceInstance.<InstanceDetails>builder()
    .name("myService")
    .payload(new InstanceDetails("host1", 8080))
    .address("192.168.1.100")
    .port(8080)
    .build();

// 服务注册
ServiceDiscovery<InstanceDetails> serviceDiscovery = ServiceDiscoveryBuilder.builder(InstanceDetails.class)
    .client(client)
    .basePath("/services")
    .serializer(new JsonInstanceSerializer<>(InstanceDetails.class))
    .build();

serviceDiscovery.start();
serviceDiscovery.registerService(instance);

// 服务发现
ServiceProvider<InstanceDetails> provider = serviceDiscovery.serviceProviderBuilder()
    .serviceName("myService")
    .build();

provider.start();

// 获取所有服务实例
Collection<ServiceInstance<InstanceDetails>> instances = provider.getAllInstances();

// 获取一个服务实例（负载均衡）
ServiceInstance<InstanceDetails> instance = provider.getInstance();
```

### 7.3 使用场景

- ✅ 微服务注册与发现
- ✅ 动态服务路由
- ✅ 服务健康检查
- ✅ 服务负载均衡

---

## 8. 缓存（Cache）

### 8.1 功能说明

**用途**：监听 ZooKeeper 节点的变化并缓存数据，适用于配置管理和数据同步

**实现方式**：基于 ZooKeeper Watch 机制

### 8.2 缓存类型

#### 8.2.1 节点缓存（NodeCache）

**特点**：
- 缓存单个节点的数据
- 自动监听节点变化
- 支持初始化和更新回调

**示例**：

```java
NodeCache nodeCache = new NodeCache(client, "/config/myConfig");
nodeCache.start();

// 监听变化
nodeCache.getListenable().addListener(new NodeCacheListener() {
    @Override
    public void nodeChanged() throws Exception {
        ChildData currentData = nodeCache.getCurrentData();
        if (currentData != null) {
            System.out.println("Node data: " + new String(currentData.getData()));
        }
    }
});

// 获取当前数据
ChildData currentData = nodeCache.getCurrentData();
if (currentData != null) {
    byte[] data = currentData.getData();
}
```

#### 8.2.2 路径缓存（PathChildrenCache）

**特点**：
- 缓存子节点的数据
- 监听子节点的增删改
- 支持初始化和更新回调

**示例**：

```java
PathChildrenCache pathCache = new PathChildrenCache(client, "/config", true);
pathCache.start(PathChildrenCache.StartMode.BUILD_INITIAL_CACHE);

// 监听变化
pathCache.getListenable().addListener(new PathChildrenCacheListener() {
    @Override
    public void childEvent(CuratorFramework client, PathChildrenCacheEvent event) throws Exception {
        switch (event.getType()) {
            case CHILD_ADDED:
                System.out.println("Child added: " + event.getData().getPath());
                break;
            case CHILD_UPDATED:
                System.out.println("Child updated: " + event.getData().getPath());
                break;
            case CHILD_REMOVED:
                System.out.println("Child removed: " + event.getData().getPath());
                break;
        }
    }
});

// 获取所有子节点
List<ChildData> children = pathCache.getCurrentData();
```

#### 8.2.3 树缓存（TreeCache）

**特点**：
- 缓存整个子树的数据
- 监听所有子节点的变化
- 功能最强大，但性能开销较大

**示例**：

```java
TreeCache treeCache = new TreeCache(client, "/config");
treeCache.start();

// 监听变化
treeCache.getListenable().addListener(new TreeCacheListener() {
    @Override
    public void childEvent(CuratorFramework client, TreeCacheEvent event) throws Exception {
        switch (event.getType()) {
            case NODE_ADDED:
                System.out.println("Node added: " + event.getData().getPath());
                break;
            case NODE_UPDATED:
                System.out.println("Node updated: " + event.getData().getPath());
                break;
            case NODE_REMOVED:
                System.out.println("Node removed: " + event.getData().getPath());
                break;
        }
    }
});

// 获取所有节点
Collection<ChildData> allNodes = treeCache.getCurrentChildren("/config");
```

### 8.3 使用场景

- ✅ 配置中心（实时配置更新）
- ✅ 服务发现（服务列表缓存）
- ✅ 数据同步（主从数据同步）
- ✅ 配置热更新

---

## 9. 信号量（Semaphore）

### 9.1 功能说明

**用途**：控制同时访问资源的线程数量（限流）

**实现方式**：基于 ZooKeeper 临时节点

### 9.2 使用示例

```java
// 创建信号量（最多10个许可）
InterProcessSemaphoreV2 semaphore = new InterProcessSemaphoreV2(
    client, "/semaphores/mySemaphore", 10);

// 获取许可
Lease lease = semaphore.acquire();
try {
    // 执行业务逻辑（最多10个线程同时执行）
    doSomething();
} finally {
    // 释放许可
    semaphore.returnLease(lease);
}

// 或者使用超时获取
Lease lease = semaphore.acquire(5, TimeUnit.SECONDS);
if (lease != null) {
    try {
        doSomething();
    } finally {
        semaphore.returnLease(lease);
    }
}
```

### 9.3 使用场景

- ✅ 限流（API 限流）
- ✅ 资源池管理
- ✅ 并发控制
- ✅ 连接池限制

---

## 10. 栅栏（Barrier）

### 10.1 功能说明

**用途**：协调多个进程，等待所有进程到达某个点后再继续执行

**实现方式**：基于 ZooKeeper 节点

### 10.2 栅栏类型

#### 10.2.1 分布式栅栏（DistributedBarrier）

**特点**：
- 等待所有进程到达
- 统一释放

**示例**：

```java
DistributedBarrier barrier = new DistributedBarrier(client, "/barriers/myBarrier");

// 等待所有进程到达
barrier.waitOnBarrier();

// 主进程设置栅栏
barrier.setBarrier();

// 主进程移除栅栏（释放所有等待的进程）
barrier.removeBarrier();
```

#### 10.2.2 分布式双栅栏（DistributedDoubleBarrier）

**特点**：
- 支持进入和退出两个阶段
- 自动管理

**示例**：

```java
// 创建双栅栏（需要5个进程）
DistributedDoubleBarrier doubleBarrier = new DistributedDoubleBarrier(
    client, "/barriers/myDoubleBarrier", 5);

try {
    // 进入栅栏（等待所有5个进程到达）
    doubleBarrier.enter();
    
    // 执行业务逻辑（所有进程同时执行）
    doSomething();
    
} finally {
    // 退出栅栏（等待所有5个进程完成）
    doubleBarrier.leave();
}
```

### 10.3 使用场景

- ✅ 分布式计算（MapReduce）
- ✅ 批量任务协调
- ✅ 分布式测试
- ✅ 同步点协调

---

## 11. 分布式原子值（Atomic Value）

### 11.1 功能说明

**用途**：提供分布式环境下的原子操作

**实现方式**：基于 ZooKeeper 节点和版本号

### 11.2 使用示例

```java
// 分布式原子长整型
DistributedAtomicLong atomicLong = new DistributedAtomicLong(
    client, "/atomic/myLong", new RetryNTimes(3, 1000));

// 获取当前值
AtomicValue<Long> current = atomicLong.get();
System.out.println("Current value: " + current.value());

// 增加并获取
AtomicValue<Long> result = atomicLong.add(10L);
if (result.succeeded()) {
    System.out.println("New value: " + result.postValue());
}

// CAS 操作
AtomicValue<Long> casResult = atomicLong.compareAndSet(100L, 200L);
if (casResult.succeeded()) {
    System.out.println("CAS succeeded");
}
```

### 11.3 使用场景

- ✅ 分布式 ID 生成
- ✅ 分布式计数器
- ✅ 原子操作需求
- ✅ 版本控制

---

## 12. 节点监听（Node Watcher）

### 12.1 功能说明

**用途**：监听 ZooKeeper 节点的变化

**实现方式**：基于 ZooKeeper Watch 机制

### 12.2 使用示例

```java
// 使用 Curator 的 Watcher
client.getData().usingWatcher(new Watcher() {
    @Override
    public void process(WatchedEvent event) {
        switch (event.getType()) {
            case NodeCreated:
                System.out.println("Node created: " + event.getPath());
                break;
            case NodeDeleted:
                System.out.println("Node deleted: " + event.getPath());
                break;
            case NodeDataChanged:
                System.out.println("Node data changed: " + event.getPath());
                break;
        }
    }
}).forPath("/myNode");
```

### 12.3 使用场景

- ✅ 配置变更监听
- ✅ 服务状态监听
- ✅ 数据同步
- ✅ 事件通知

---

## 13. 事务支持（Transaction）

### 13.1 功能说明

**用途**：在一个原子操作中执行多个节点操作

**实现方式**：基于 ZooKeeper 事务 API

### 13.2 使用示例

```java
// 创建事务
CuratorTransaction transaction = client.inTransaction();

// 添加操作
transaction.create()
    .forPath("/path1", "data1".getBytes())
    .and()
    .setData()
    .forPath("/path2", "data2".getBytes())
    .and()
    .delete()
    .forPath("/path3")
    .and();

// 提交事务（原子操作）
TransactionResult result = transaction.commit();

// 检查结果
for (CuratorTransactionResult r : result) {
    System.out.println("Operation: " + r.getType() + ", Path: " + r.getForPath());
}
```

### 13.3 使用场景

- ✅ 批量操作
- ✅ 数据一致性保证
- ✅ 原子性操作需求
- ✅ 分布式事务

---

## 14. 测试工具（Testing）

### 14.1 功能说明

**用途**：提供用于测试的嵌入式 ZooKeeper 服务器

**实现方式**：内嵌 ZooKeeper 服务器

### 14.2 使用示例

```java
// 创建测试服务器
TestingServer testingServer = new TestingServer(2181, true);

// 获取连接字符串
String connectString = testingServer.getConnectString();

// 创建客户端
CuratorFramework client = CuratorFrameworkFactory.newClient(
    connectString, new RetryNTimes(3, 1000));
client.start();

// 执行测试...

// 关闭
client.close();
testingServer.close();
```

### 14.3 使用场景

- ✅ 单元测试
- ✅ 集成测试
- ✅ 本地开发测试
- ✅ CI/CD 测试

---

## 15. 功能对比总结

### 15.1 功能列表

| 功能 | 类名 | 用途 | 使用频率 |
|------|------|------|----------|
| **分布式锁** | InterProcessMutex | 互斥访问 | ⭐⭐⭐⭐⭐ |
| **读写锁** | InterProcessReadWriteLock | 读写分离 | ⭐⭐⭐⭐ |
| **信号量** | InterProcessSemaphoreV2 | 限流控制 | ⭐⭐⭐⭐ |
| **领导者选举** | LeaderSelector/LeaderLatch | 主从选举 | ⭐⭐⭐⭐⭐ |
| **分布式队列** | DistributedQueue | 任务队列 | ⭐⭐⭐ |
| **分布式计数器** | SharedCount/DistributedAtomicLong | 计数统计 | ⭐⭐⭐ |
| **服务发现** | ServiceDiscovery | 服务注册发现 | ⭐⭐⭐⭐ |
| **节点缓存** | NodeCache | 单节点缓存 | ⭐⭐⭐⭐ |
| **路径缓存** | PathChildrenCache | 子节点缓存 | ⭐⭐⭐⭐ |
| **树缓存** | TreeCache | 子树缓存 | ⭐⭐⭐ |
| **栅栏** | DistributedBarrier | 进程协调 | ⭐⭐ |
| **原子值** | DistributedAtomicLong | 原子操作 | ⭐⭐⭐ |
| **事务** | CuratorTransaction | 批量操作 | ⭐⭐⭐ |

### 15.2 常用功能推荐

#### 最常用（⭐⭐⭐⭐⭐）

1. **分布式锁（InterProcessMutex）**
   - 用途最广泛
   - 实现简单
   - 可靠性高

2. **领导者选举（LeaderSelector）**
   - 主从架构必备
   - 定时任务常用
   - 配置管理常用

#### 常用（⭐⭐⭐⭐）

3. **服务发现（ServiceDiscovery）**
   - 微服务架构必备
   - 动态服务管理

4. **缓存（NodeCache/PathChildrenCache）**
   - 配置中心常用
   - 实时数据同步

5. **读写锁（InterProcessReadWriteLock）**
   - 读写分离场景
   - 提高并发性能

#### 特殊场景（⭐⭐⭐）

6. **分布式队列（DistributedQueue）**
   - 任务调度
   - 消息队列

7. **分布式计数器（SharedCount）**
   - 统计计数
   - 限流控制

8. **信号量（InterProcessSemaphoreV2）**
   - 限流
   - 资源池管理

### 15.3 功能选择指南

| 需求 | 推荐功能 | 说明 |
|------|----------|------|
| **互斥访问** | InterProcessMutex | 分布式锁 |
| **主从选举** | LeaderSelector | 领导者选举 |
| **服务注册发现** | ServiceDiscovery | 服务发现 |
| **配置管理** | NodeCache/PathChildrenCache | 节点缓存 |
| **限流控制** | InterProcessSemaphoreV2 | 信号量 |
| **任务队列** | DistributedQueue | 分布式队列 |
| **计数统计** | SharedCount | 共享计数器 |
| **进程协调** | DistributedBarrier | 栅栏 |
| **原子操作** | DistributedAtomicLong | 原子值 |
| **批量操作** | CuratorTransaction | 事务 |

---

## 16. 最佳实践

### 16.1 连接管理

```java
// 推荐：使用连接池
CuratorFramework client = CuratorFrameworkFactory.builder()
    .connectString("127.0.0.1:2181")
    .sessionTimeoutMs(5000)
    .connectionTimeoutMs(3000)
    .retryPolicy(new ExponentialBackoffRetry(1000, 3))
    .build();

client.start();

// 应用关闭时关闭客户端
Runtime.getRuntime().addShutdownHook(new Thread(() -> {
    client.close();
}));
```

### 16.2 重试策略

```java
// 指数退避重试（推荐）
RetryPolicy retryPolicy = new ExponentialBackoffRetry(1000, 3);

// 固定间隔重试
RetryPolicy retryPolicy = new RetryNTimes(3, 1000);

// 直到成功重试
RetryPolicy retryPolicy = new RetryUntilElapsed(5000, 1000);
```

### 16.3 异常处理

```java
try {
    lock.acquire();
    // 执行业务逻辑
} catch (Exception e) {
    // 处理异常
    log.error("Lock acquire failed", e);
} finally {
    try {
        if (lock.isAcquiredInThisProcess()) {
            lock.release();
        }
    } catch (Exception e) {
        log.error("Lock release failed", e);
    }
}
```

### 16.4 资源清理

```java
// 确保资源正确释放
InterProcessMutex lock = new InterProcessMutex(client, "/locks/myLock");
try {
    lock.acquire();
    // 执行业务逻辑
} finally {
    // 确保释放锁
    if (lock.isAcquiredInThisProcess()) {
        lock.release();
    }
}
```

---

## 17. 总结

Apache Curator 提供了丰富的分布式系统工具和模式：

1. **核心功能**：
   - 分布式锁（最常用）
   - 领导者选举（主从架构必备）
   - 服务发现（微服务必备）

2. **辅助功能**：
   - 缓存（配置管理）
   - 队列（任务调度）
   - 计数器（统计限流）
   - 信号量（限流控制）

3. **高级功能**：
   - 栅栏（进程协调）
   - 原子值（原子操作）
   - 事务（批量操作）

4. **开发工具**：
   - 测试工具（本地测试）

**选择建议**：
- **大多数场景**：分布式锁 + 领导者选举
- **微服务架构**：服务发现 + 配置缓存
- **特殊需求**：根据具体场景选择对应功能

---

**文档版本**：v1.0  
**最后更新**：2024年  
**作者**：Zookeeper-study 项目组

