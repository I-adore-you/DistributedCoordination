#!/bin/bash

echo "=== 检查 ZooKeeper 集群状态 ==="
echo ""

# 1. 检查容器状态
echo "1. 容器状态："
docker ps --filter "name=zk" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# 2. 检查端口是否可访问
echo "2. 端口检查："
for port in 2181 2182 2183; do
    if nc -z localhost $port 2>/dev/null; then
        echo "✓ 端口 $port 可访问"
    else
        echo "✗ 端口 $port 不可访问"
    fi
done
echo ""

# 3. 检查节点健康状态（使用四字命令）
echo "3. 节点健康检查："
for i in 1 2 3; do
    container="zk${i}-3.4.6"
    echo -n "节点 zk${i}: "
    result=$(docker exec $container sh -c "echo ruok | nc localhost 2181" 2>/dev/null)
    if [ "$result" = "imok" ]; then
        echo "✓ 健康 (imok)"
    else
        echo "? 状态未知"
    fi
done
echo ""

# 4. 尝试连接测试
echo "4. 连接测试："
echo "可以直接执行以下命令连接集群："
echo ""
echo "  docker exec -it zk1-3.4.6 zkCli.sh -server zk1:2181,zk2:2181,zk3:2181"
echo ""
echo "或者连接单个节点："
echo "  docker exec -it zk1-3.4.6 zkCli.sh -server zk1:2181"
echo ""

