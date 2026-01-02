import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re

# 读取pos文件，跳过image部分
def read_pos_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取elements部分，跳过image部分
    elements_pattern = r'"elements":\s*\{([\s\S]*?)\}\s*\}'
    match = re.search(elements_pattern, content)
    
    if match:
        elements_str = '{"elements": {' + match.group(1) + '}}'
        try:
            elements_data = json.loads(elements_str)
            return elements_data
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return None
    else:
        print("未找到elements部分")
        return None

# 获取节点样式
def get_node_style(element_data):
    style = []
    
    # 基础形状
    if element_data['name'] == 'round':
        style.append('rounded=1')
    
    # 文本样式
    style.append('whiteSpace=wrap')
    style.append('html=1')
    
    # 填充颜色
    if 'fillStyle' in element_data and element_data['fillStyle']:
        fill_color = element_data['fillStyle'].get('color', '#ffffff')
        style.append(f'fillColor={fill_color}')
    else:
        style.append('fillColor=#ffffff')
    
    # 边框颜色
    if 'lineStyle' in element_data and element_data['lineStyle'] and 'color' in element_data['lineStyle']:
        stroke_color = element_data['lineStyle']['color']
        style.append(f'strokeColor={stroke_color}')
    else:
        style.append('strokeColor=#000000')
    
    return ';'.join(style)

# 生成drawio XML
def generate_drawio_xml(elements_data):
    # 创建根元素
    mxfile = ET.Element('mxfile', {
        'host': 'app.diagrams.net',
        'modified': '2026-01-01T00:00:00.000Z',
        'agent': 'pos_to_drawio_converter',
        'version': '24.8.3',
        'etag': 'converted_from_pos',
        'type': 'device'
    })
    
    # 创建diagram元素
    diagram = ET.SubElement(mxfile, 'diagram', {
        'name': 'Page-1',
        'id': 'converted-diagram'
    })
    
    # 创建mxGraphModel元素
    mx_graph_model = ET.SubElement(diagram, 'mxGraphModel', {
        'dx': '2000',
        'dy': '2000',
        'grid': '1',
        'gridSize': '10',
        'guides': '1',
        'tooltips': '1',
        'connect': '1',
        'arrows': '1',
        'fold': '1',
        'page': '1',
        'pageScale': '1',
        'pageWidth': '827',
        'pageHeight': '1169',
        'math': '0',
        'shadow': '0'
    })
    
    # 创建root元素
    root = ET.SubElement(mx_graph_model, 'root')
    
    # 创建默认节点
    ET.SubElement(root, 'mxCell', {'id': '0'})
    ET.SubElement(root, 'mxCell', {'id': '1', 'parent': '0'})
    
    elements = elements_data.get('elements', {})
    
    print(f"Found {len(elements)} elements in pos file")
    
    # 处理节点
    nodes = {}
    for element_id, element_data in elements.items():
        if 'name' in element_data:
            if element_data['name'] == 'round' or element_data['name'] == 'rect':
                # 创建节点
                try:
                    # 提取文本
                    text = ''
                    if 'textBlock' in element_data and element_data['textBlock']:
                        text_block = element_data['textBlock'][0]
                        if 'text' in text_block:
                            text = text_block['text']
                    
                    mx_cell = ET.SubElement(root, 'mxCell', {
                        'id': element_id,
                        'value': text,
                        'style': get_node_style(element_data),
                        'parent': '1',
                        'vertex': '1'
                    })
                    
                    # 添加几何信息
                    props = element_data['props']
                    ET.SubElement(mx_cell, 'mxGeometry', {
                        'x': str(props['x']),
                        'y': str(props['y']),
                        'width': str(props['w']),
                        'height': str(props['h']),
                        'as': 'geometry'
                    })
                    
                    nodes[element_id] = mx_cell
                    print(f"Created node {element_id}")
                except Exception as e:
                    print(f"Error creating node {element_id}: {e}")
    
    print(f"Created {len(nodes)} nodes")
    
    # 处理连接线
    links_created = 0
    for element_id, element_data in elements.items():
        if 'name' in element_data and element_data['name'] == 'linker':
            try:
                # 检查源节点和目标节点是否存在
                source_id = element_data['from']['id']
                target_id = element_data['to']['id']
                
                if source_id in nodes and target_id in nodes:
                    # 创建连接线
                    mx_cell = ET.SubElement(root, 'mxCell', {
                        'id': element_id,
                        'value': element_data.get('text', ''),
                        'style': 'endArrow=classic;html=1;rounded=0;',
                        'parent': '1',
                        'source': source_id,
                        'target': target_id,
                        'edge': '1'
                    })
                    
                    # 添加几何信息
                    geometry = ET.SubElement(mx_cell, 'mxGeometry', {
                        'relative': '1',
                        'as': 'geometry'
                    })
                    
                    links_created += 1
                    print(f"Created link {element_id} from {source_id} to {target_id}")
                else:
                    print(f"Skipping link {element_id}: source {source_id} or target {target_id} not found")
            except Exception as e:
                print(f"Error creating link {element_id}: {e}")
    
    print(f"Created {links_created} links")
    
    # 返回格式化的XML
    return minidom.parseString(ET.tostring(mxfile, encoding='unicode')).toprettyxml(indent='  ')

# 主函数
def main():
    import os
    
    # 获取当前目录下的所有.pos文件
    pos_files = [f for f in os.listdir('.') if f.endswith('.pos')]
    
    for pos_file in pos_files:
        print(f'正在处理文件: {pos_file}')
        
        # 读取pos文件
        elements_data = read_pos_file(pos_file)
        
        if elements_data:
            # 生成draw.io XML
            drawio_xml = generate_drawio_xml(elements_data)
            
            # 保存为xml文件
            xml_file = pos_file.replace('.pos', '.drawio.xml')
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(drawio_xml)
            
            print(f'已生成文件: {xml_file}')
        else:
            print(f'处理文件 {pos_file} 失败')

if __name__ == '__main__':
    main()