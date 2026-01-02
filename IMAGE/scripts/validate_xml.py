import xml.etree.ElementTree as ET

# 解析生成的XML文件
try:
    tree = ET.parse('ZOOKEEPER理论.drawio.xml')
    root = tree.getroot()
    
    # 检查根元素
    if root.tag != 'mxfile':
        print("错误：不是有效的draw.io XML文件")
        exit(1)
    
    # 统计元素数量
    nodes = []
    edges = []
    
    for diagram in root.findall('.//diagram'):
        for mx_cell in diagram.findall('.//mxCell'):
            if 'vertex' in mx_cell.attrib and mx_cell.attrib['vertex'] == '1':
                nodes.append(mx_cell)
            elif 'edge' in mx_cell.attrib and mx_cell.attrib['edge'] == '1':
                edges.append(mx_cell)
    
    print(f"验证完成：")
    print(f"  - 节点数量: {len(nodes)}")
    print(f"  - 连接线数量: {len(edges)}")
    
    # 检查不同类型的节点
    print("\n节点类型统计：")
    node_types = {}
    for node in nodes:
        style = node.attrib.get('style', '')
        if 'shape=note' in style:
            node_types['note'] = node_types.get('note', 0) + 1
        elif 'shape=ellipse' in style:
            node_types['circle/round'] = node_types.get('circle/round', 0) + 1
        elif 'shape=diamond' in style:
            node_types['diamond'] = node_types.get('diamond', 0) + 1
        elif 'rounded=1' in style and 'shape=note' not in style and 'shape=ellipse' not in style:
            node_types['rounded rectangle'] = node_types.get('rounded rectangle', 0) + 1
        else:
            node_types['rectangle'] = node_types.get('rectangle', 0) + 1
    
    for node_type, count in node_types.items():
        print(f"  - {node_type}: {count}")
    
    print("\nXML文件验证通过！")
    
except Exception as e:
    print(f"验证XML文件时出错: {e}")
    exit(1)