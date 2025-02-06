import json
import os
from tqdm import tqdm

evaluate_model_name = 'fastlog'
dynamic_test_platform = 'hadoop'


def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def read_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            res = []
            content = f.read().split('\n')
            for item in content:
                if '[SUPER TAG]' in item:
                    res.append(item.split('[SUPER TAG]').pop())
                else:
                    res.append(item)
            return '\n'.join(res)
    except FileNotFoundError:
        print(f"Warning: File not found: {file_path}")
        return ""


def save_java_code(code, output_file):
    try:
        with open(output_file, 'w') as f:
            f.write(code)
    except Exception as e:
        print(f"Error saving Java code: {e}")


def get_prediction_file(item):
    try:
        file_path = item['uuidMap']['projects'][0]['unitTest'][0]['predictOutput']
        if not file_path:
            return ""
        file_path = file_path.replace(
            '/home/tby/hadoop/', '/Users/tby/Downloads/hadoop_test_platform/')
        return read_txt(file_path)
    except (KeyError, IndexError) as e:
        print(f"Error getting prediction file: {e}")
        return ""


def main():
    # 读取数据
    baseline_data = read_json(f'../../{dynamic_test_platform}/baseline.json')
    prediction_data = read_json(
        f'../../{dynamic_test_platform}/{evaluate_model_name}.json')

    # 处理每个匹配的uuid
    for baseline_item in tqdm(baseline_data):
        uuid = baseline_item['uuid']

        # 查找对应的prediction item
        prediction_item = next(
            (item for item in prediction_data if item['uuid'] == uuid), None)
        if not prediction_item:
            continue
        if prediction_item.get('successful') == False:
            continue

        try:
            # 获取预测输出文本
            baseline_output = get_prediction_file(baseline_item)
            prediction_output = get_prediction_file(prediction_item)

            # 创建uuid目录
            uuid_dir = os.path.join('../compare_files', uuid)
            os.makedirs(uuid_dir, exist_ok=True)

            # 保存Java代码
            if 'prediction' in baseline_item:
                save_java_code(baseline_item['prediction'],
                              os.path.join(uuid_dir, 'baseline.java'))
            if 'prediction' in prediction_item:
                save_java_code(prediction_item['prediction'],
                              os.path.join(uuid_dir, f'{evaluate_model_name}.java'))

            # 保存预测输出文本
            if baseline_output:
                with open(os.path.join(uuid_dir, 'baseline.txt'), 'w') as f:
                    f.write(baseline_output)
            with open(os.path.join(uuid_dir, f'{evaluate_model_name}.txt'), 'w') as f:
                f.write(prediction_output)

            # 保存JSON数据
            json_data = {
                'baseline': baseline_item,
                evaluate_model_name: prediction_item
            }
            with open(os.path.join(uuid_dir, 'data.json'), 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Error processing uuid {uuid}: {e}")
            continue


if __name__ == '__main__':
    main()
