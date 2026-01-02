import ijson

# 检查pos文件中的元素类型和数量
def check_elements(file_path):
    try:
        with open(file_path, 'rb') as f:
            # 获取实际的图表元素
            parser = ijson.items(f, 'diagram.elements.elements')
            for item in parser:
                elements = item
                break
        
        print(f"=== 检查文件: {file_path} ===")
        print(f"总元素数量: {len(elements)}")
        
        # 统计不同类型的元素
        element_types = {}
        for element_id, element_data in elements.items():
            element_type = element_data['name']
            if element_type in element_types:
                element_types[element_type] += 1
            else:
                element_types[element_type] = 1
        
        print(f"元素类型统计:")
        for element_type, count in element_types.items():
            print(f"  {element_type}: {count}个")
        
        # 查看每种类型的一个示例
        print(f"\n每种类型的示例:")
        seen_types = set()
        for element_id, element_data in elements.items():
            element_type = element_data['name']
            if element_type not in seen_types:
                print(f"\n{element_type} 示例:")
                print(f"  ID: {element_id}")
                print(f"  主要属性: {list(element_data.keys())}")
                
                # 打印一些关键属性
                if 'props' in element_data:
                    print(f"  位置大小: x={element_data['props'].get('x', 'N/A')}, y={element_data['props'].get('y', 'N/A')}, w={element_data['props'].get('w', 'N/A')}, h={element_data['props'].get('h', 'N/A')}")
                
                if 'textBlock' in element_data and element_data['textBlock']:
                    text_block = element_data['textBlock'][0]
                    if 'text' in text_block:
                        print(f"  文本: {text_block['text']}")
                
                if element_type == 'linker':
                    if 'from' in element_data and 'to' in element_data:
                        print(f"  连接: 从 {element_data['from'].get('id', 'N/A')} 到 {element_data['to'].get('id', 'N/A')}")
                
                seen_types.add(element_type)
                
            if len(seen_types) == len(element_types):
                break
        
        return elements, element_types
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return None, None

# 主函数
def main():
    import os
    
    # 获取当前目录下的所有.pos文件
    pos_files = [f for f in os.listdir('.') if f.endswith('.pos')]
    
    for pos_file in pos_files:
        check_elements(pos_file)

if __name__ == '__main__':
    main()