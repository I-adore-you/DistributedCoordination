
package com.msb.zookeeper.curator;

import org.apache.curator.framework.CuratorFramework;
import org.apache.curator.framework.CuratorFrameworkFactory;
import org.apache.curator.framework.recipes.leader.LeaderLatch;
import org.apache.curator.framework.recipes.leader.LeaderLatchListener;
import org.apache.curator.retry.ExponentialBackoffRetry;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Curator 领导者选举演示 - LeaderLatch 方式
 *
 * 特点：
 * 1. 简单的 Leader 选举
 * 2. 一旦成为 Leader，会一直保持直到主动关闭
 * 3. 需要手动检查是否为 Leader
 *
 * 运行前请确保 ZooKeeper 集群已启动：
 * docker-compose -f docker-compose-zk363-static.yml up -d
 */
public class LeaderLatchDemo {

    private static final String ZK_ADDRESS = "localhost:2181,localhost:2182,localhost:2183";
    private static final String LEADER_PATH = "/curator/latch";

    public static void main(String[] args) throws Exception {
        // 模拟 3 个客户端竞争 Leader
        int clientCount = 3;
        List<CuratorFramework> clients = new ArrayList<>();
        List<LeaderLatch> latches = new ArrayList<>();

        for (int i = 0; i < clientCount; i++) {
            final String clientId = "Client-" + i;

            // 创建 Curator 客户端
            CuratorFramework client = CuratorFrameworkFactory.builder()
                    .connectString(ZK_ADDRESS)
                    .sessionTimeoutMs(30000)
                    .connectionTimeoutMs(15000)
                    .retryPolicy(new ExponentialBackoffRetry(1000, 3))
                    .build();

            client.start();
            clients.add(client);

            // 创建 LeaderLatch，传入客户端ID用于标识
            LeaderLatch latch = new LeaderLatch(client, LEADER_PATH, clientId);

            // 添加监听器
            latch.addListener(new LeaderLatchListener() {
                @Override
                public void isLeader() {
                    System.out.println("====================================");
                    System.out.println(clientId + " 成为 Leader！");
                    System.out.println("====================================");
                }

                @Override
                public void notLeader() {
                    System.out.println(clientId + " 失去 Leader 身份");
                }
            });

            latch.start();
            latches.add(latch);
            System.out.println(clientId + " 已加入选举");
        }

        // 等待选举完成
        TimeUnit.SECONDS.sleep(3);

        // 检查当前 Leader
        System.out.println("\n=== 当前 Leader 状态 ===");
        for (int i = 0; i < latches.size(); i++) {
            LeaderLatch latch = latches.get(i);
            System.out.println("Client-" + i + " isLeader: " + latch.hasLeadership());
        }

        // 获取当前 Leader 信息
        LeaderLatch anyLatch = latches.get(0);
        System.out.println("\n当前 Leader ID: " + anyLatch.getLeader().getId());

        // 模拟 Leader 宕机（关闭第一个成为 Leader 的客户端）
        System.out.println("\n=== 模拟 Leader 宕机 ===");
        for (int i = 0; i < latches.size(); i++) {
            if (latches.get(i).hasLeadership()) {
                System.out.println("关闭 Client-" + i + " (当前 Leader)");
                latches.get(i).close();
                clients.get(i).close();
                break;
            }
        }

        // 等待重新选举
        TimeUnit.SECONDS.sleep(3);

        // 再次检查 Leader
        System.out.println("\n=== 重新选举后的 Leader 状态 ===");
        for (int i = 0; i < latches.size(); i++) {
            LeaderLatch latch = latches.get(i);
            if (latch.getState() == LeaderLatch.State.STARTED) {
                System.out.println("Client-" + i + " isLeader: " + latch.hasLeadership());
            }
        }

        // 让程序运行一段时间
        TimeUnit.SECONDS.sleep(5);

        // 清理资源
        System.out.println("\n清理资源...");
        for (int i = 0; i < latches.size(); i++) {
            LeaderLatch latch = latches.get(i);
            if (latch.getState() == LeaderLatch.State.STARTED) {
                latch.close();
            }
        }
        for (CuratorFramework client : clients) {
            if (client.getZookeeperClient().isConnected()) {
                client.close();
            }
        }
        System.out.println("演示结束");
    }
}
