import ijson
import xml.etree.ElementTree as ET
from xml.dom import minidom

# 使用ijson流式读取pos文件，只提取elements部分
def read_pos_file(file_path):
    elements = {}
    
    try:
        with open(file_path, 'rb') as f:
            # 获取实际的图表元素（在diagram.elements.elements路径下）
            parser = ijson.items(f, 'diagram.elements.elements')
            for item in parser:
                # 这应该会得到一个包含所有元素的字典
                elements = item
                break
        
        return {'elements': elements}
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return None

# 获取节点样式
def get_node_style(element_data):
    style = []
    
    # 基础形状
    element_type = element_data['name']
    
    if element_type == 'round' or element_type == 'circle':
        style.append('rounded=1')
        style.append('shape=ellipse')
    elif element_type == 'rect' or element_type == 'rectangle':
        style.append('rounded=0')
    elif element_type == 'note':
        style.append('rounded=1')
        style.append('shape=note')
        style.append('fillColor=#fff0c2')
    elif element_type == 'roundRectangle':
        style.append('rounded=1')
        style.append('arcSize=20')
    elif element_type == 'diamond':
        style.append('shape=diamond')
    elif element_type in ['singleRightArrow', 'singleLeftArrow']:
        style.append('shape=process')
        style.append('rounded=0')
    
    # 文本样式
    style.append('whiteSpace=wrap')
    style.append('html=1')
    
    # 辅助函数：将RGB颜色转换为十六进制
    def rgb_to_hex(color_val):
        if isinstance(color_val, list) and len(color_val) >= 3:
            # 处理RGB数组格式 [r, g, b]
            r, g, b = color_val[:3]
            # 确保颜色值在0-255范围内
            r = max(0, min(255, int(r)))
            g = max(0, min(255, int(g)))
            b = max(0, min(255, int(b)))
            return f'#{r:02x}{g:02x}{b:02x}'
        elif isinstance(color_val, str) and color_val.startswith('#'):
            # 已经是十六进制格式
            return color_val
        else:
            # 默认白色
            return '#ffffff'
    
    # 填充颜色（如果不是特殊形状）
    if element_type not in ['note']:  # note已经有默认填充色
        if 'fillStyle' in element_data and element_data['fillStyle']:
            fill_color_val = element_data['fillStyle'].get('color', [255, 255, 255])
            fill_color = rgb_to_hex(fill_color_val)
            # 避免黑色背景导致文本不可见
            if fill_color == '#000000':
                fill_color = '#ffffff'
            style.append(f'fillColor={fill_color}')
        else:
            style.append('fillColor=#ffffff')
    
    # 边框颜色
    if 'lineStyle' in element_data and element_data['lineStyle'] and 'color' in element_data['lineStyle']:
        stroke_color_val = element_data['lineStyle']['color']
        stroke_color = rgb_to_hex(stroke_color_val)
        style.append(f'strokeColor={stroke_color}')
    elif element_type not in ['note']:  # note使用默认边框颜色
        style.append('strokeColor=#000000')
    
    # 文本颜色
    style.append('fontColor=#000000')  # 设置黑色文本确保可见性
    
    # 边框宽度
    if 'lineStyle' in element_data and element_data['lineStyle'] and 'width' in element_data['lineStyle']:
        stroke_width = element_data['lineStyle']['width']
        style.append(f'strokeWidth={stroke_width}')
    
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
    
    # 支持的节点类型
    supported_node_types = ['round', 'rect', 'rectangle', 'note', 'roundRectangle', 
                           'diamond', 'singleRightArrow', 'singleLeftArrow', 'circle']
                           
    for element_id, element_data in elements.items():
        if element_data['name'] in supported_node_types:
            # 创建节点
            try:
                # 提取文本
                text = ''
                if 'textBlock' in element_data and element_data['textBlock']:
                    text_block = element_data['textBlock'][0]
                    if 'text' in text_block:
                        text = text_block['text']
                        # 转换HTML标签
                        text = text.replace('<div>', '\n').replace('</div>', '')
                        text = text.replace('&nbsp;', ' ')
                
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
                print(f"Created node {element_id}: {element_data['name']} - {text[:50]}{'...' if len(text) > 50 else ''}")
            except Exception as e:
                print(f"Error creating node {element_id}: {e}")
                import traceback
                traceback.print_exc()
    
    print(f"Created {len(nodes)} nodes")
    
    # 处理连接线
    links_created = 0
    for element_id, element_data in elements.items():
        if element_data['name'] == 'linker':
            try:
                # 检查源节点和目标节点是否存在
                source_id = element_data['from']['id']
                target_id = element_data['to']['id']
                
                if source_id in nodes and target_id in nodes:
                    # 获取连接线上的文本
                    text = ''
                    if 'textBlock' in element_data and element_data['textBlock']:
                        text_block = element_data['textBlock'][0]
                        if 'text' in text_block:
                            text = text_block['text']
                            # 转换HTML标签
                            text = text.replace('<div>', '\n').replace('</div>', '')
                            text = text.replace('&nbsp;', ' ')
                    
                    # 设置连接线样式
                    style = ['endArrow=classic', 'html=1', 'rounded=0', 'fillColor=none']  # 连接线无填充
                    
                    # 添加线条样式
                    if 'lineStyle' in element_data and element_data['lineStyle']:
                        line_style = element_data['lineStyle']
                        if 'width' in line_style:
                            style.append(f'strokeWidth={line_style["width"]}')
                        if 'color' in line_style:
                            stroke_color_val = line_style['color']
                            # 辅助函数：将RGB颜色转换为十六进制
                            def rgb_to_hex(color_val):
                                if isinstance(color_val, list) and len(color_val) >= 3:
                                    # 处理RGB数组格式 [r, g, b]
                                    r, g, b = color_val[:3]
                                    # 确保颜色值在0-255范围内
                                    r = max(0, min(255, int(r)))
                                    g = max(0, min(255, int(g)))
                                    b = max(0, min(255, int(b)))
                                    return f'#{r:02x}{g:02x}{b:02x}'
                                elif isinstance(color_val, str) and color_val.startswith('#'):
                                    # 已经是十六进制格式
                                    return color_val
                                else:
                                    # 默认黑色边框
                                    return '#000000'
                            
                            stroke_color = rgb_to_hex(stroke_color_val)
                            style.append(f'strokeColor={stroke_color}')
                    
                    # 文本颜色
                    style.append('fontColor=#000000')  # 设置黑色文本确保可见性
                    
                    # 创建连接线
                    mx_cell = ET.SubElement(root, 'mxCell', {
                        'id': element_id,
                        'value': text,
                        'style': ';'.join(style),
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
                    print(f"Created link {element_id} from {source_id} to {target_id} {'- ' + text[:30] if text else ''}")
                else:
                    print(f"Skipping link {element_id}: source {source_id} or target {target_id} not found")
            except Exception as e:
                print(f"Error creating link {element_id}: {e}")
                import traceback
                traceback.print_exc()
    
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