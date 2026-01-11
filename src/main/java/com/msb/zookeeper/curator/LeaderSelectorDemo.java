package com.msb.zookeeper.curator;

import org.apache.curator.framework.CuratorFramework;
import org.apache.curator.framework.CuratorFrameworkFactory;
import org.apache.curator.framework.recipes.leader.LeaderSelector;
import org.apache.curator.framework.recipes.leader.LeaderSelectorListenerAdapter;
import org.apache.curator.retry.ExponentialBackoffRetry;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Curator 领导者选举演示 - LeaderSelector 方式（推荐）
 *
 * 特点：
 * 1. 自动重新选举（autoRequeue）
 * 2. 支持 Leader 回调
 * 3. takeLeadership 方法返回时自动放弃 Leader
 *
 * 运行前请确保 ZooKeeper 集群已启动：
 * docker-compose -f docker-compose-zk363-static.yml up -d
 */
public class LeaderSelectorDemo {

    private static final String ZK_ADDRESS = "localhost:2181,localhost:2182,localhost:2183";
    private static final String LEADER_PATH = "/curator/leader";

    public static void main(String[] args) throws Exception {
        // 模拟 3 个客户端竞争 Leader
        int clientCount = 3;
        List<CuratorFramework> clients = new ArrayList<>();
        List<LeaderSelector> selectors = new ArrayList<>();

        for (int i = 0; i < clientCount; i++) {
            final String clientName = "Client-" + i;

            // 创建 Curator 客户端
            CuratorFramework client = CuratorFrameworkFactory.builder()
                    .connectString(ZK_ADDRESS)
                    .sessionTimeoutMs(30000)
                    .connectionTimeoutMs(15000)
                    .retryPolicy(new ExponentialBackoffRetry(1000, 3))
                    .build();

            client.start();
            clients.add(client);

            // 创建 LeaderSelector
            LeaderSelector selector = new LeaderSelector(client, LEADER_PATH,
                    new LeaderSelectorListenerAdapter() {
                        @Override
                        public void takeLeadership(CuratorFramework client) throws Exception {
                            System.out.println("====================================");
                            System.out.println(clientName + " 成为 Leader！开始执行任务...");
                            System.out.println("====================================");

                            // 模拟 Leader 执行任务（持有 5 秒）
                            doLeaderWork(clientName);

                            System.out.println(clientName + " 任务完成，放弃 Leader 身份");
                            // 方法返回时，自动放弃 Leader，触发重新选举
                        }
                    });

            // 自动重新参与选举（放弃 Leader 后会重新排队）
            selector.autoRequeue();
            selector.start();
            selectors.add(selector);

            System.out.println(clientName + " 已加入选举");
        }

        // 让程序运行 30 秒，观察选举过程
        System.out.println("\n程序运行 30 秒，观察多轮选举...\n");
        TimeUnit.SECONDS.sleep(30);

        // 清理资源
        System.out.println("\n清理资源...");
        for (LeaderSelector selector : selectors) {
            selector.close();
        }
        for (CuratorFramework client : clients) {
            client.close();
        }
        System.out.println("演示结束");
    }

    /**
     * 模拟 Leader 执行的业务逻辑
     */
    private static void doLeaderWork(String clientName) throws InterruptedException {
        for (int i = 1; i <= 5; i++) {
            System.out.println("  [" + clientName + "] 执行任务 " + i + "/5");
            TimeUnit.SECONDS.sleep(1);
        }
    }
}
