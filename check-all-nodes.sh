#!/bin/bash
# ZooKeeper 集群节点状态检查脚本

echo "=== ZooKeeper 集群节点状态检查 ==="
echo ""

for i in 1 2 3; do
    container="zk${i}-3.4.6"
    port=$((2180 + i))
    
    echo "--- 节点 zk${i} (端口 ${port}) ---"
    
    # 检查容器是否运行
    if ! docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
        echo "✗ 容器未运行"
        echo ""
        continue
    fi
    
    # 检查节点角色（使用 zkServer.sh status）
    status_output=$(docker exec $container zkServer.sh status 2>&1)
    mode=$(echo "$status_output" | grep "Mode:" | awk '{print $2}')
    
    if [ -n "$mode" ]; then
        if [ "$mode" = "leader" ]; then
            echo "  角色: ⭐ Leader (主节点)"
        elif [ "$mode" = "follower" ]; then
            echo "  角色: 👥 Follower (从节点)"
        else
            echo "  角色: $mode"
        fi
        echo "✓ 健康状态: 正常"
    else
        # 如果 zkServer.sh 失败，尝试从日志判断
        echo "  角色: 检查中..."
        if docker logs $container 2>&1 | grep -q "Leader"; then
            echo "  角色: ⭐ Leader (从日志判断)"
            echo "✓ 健康状态: 正常"
        elif docker logs $container 2>&1 | grep -q "following"; then
            echo "  角色: 👥 Follower (从日志判断)"
            echo "✓ 健康状态: 正常"
        else
            echo "✗ 健康状态: 无法确定"
        fi
    fi
    
    echo ""
done

echo "=== 快速连接命令 ==="
echo "连接集群: docker exec -it zk1-3.4.6 zkCli.sh -server zk1:2181,zk2:2181,zk3:2181"
echo "连接 zk1: docker exec -it zk1-3.4.6 zkCli.sh -server localhost:2181"
echo ""

