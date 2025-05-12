import json
from evaluate_tool import get_gro_mes, extract_static_and_vars, get_logging_greedy, check_vars_accuracy
from sacrebleu import sentence_bleu
from tabulate import tabulate
from rouge import Rouge

def read_json_sample(json_file_path):  
  try:
    with open(json_file_path, 'r', encoding='utf-8') as f:
      data = json.load(f)
      
    # 如果数据是列表，显示第一个样本
    if isinstance(data, list) and len(data) > 0:
      pass
      # print("First sample from the JSON file:")
      # print(json.dumps(data[0], indent=2, ensure_ascii=False))
    # 如果数据是字典，直接显示
    elif isinstance(data, dict):
      print("JSON content:")
      print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
      print("No valid data found in the JSON file")

    return data
      
  except FileNotFoundError:
    print(f"Error: File {json_file_path} not found")
  except json.JSONDecodeError:
    print("Error: Invalid JSON format")



def evaluation_greedy(input_file_path, tool_name):
    pos_count,pos_related_count, level_count, message_count, vars_accuracy_count = 0, 0, 0, 0, 0
    data_num = 0
    validate_num = 0
    cat_dict = {'trace': 0, 'debug': 1, 'info': 2, 'warn': 3, 'error': 4, 'fatal': 5}
    level_distance_dict = {}
    static_message_rouge = {
      'rouge-1': 0,
      'rouge-2': 0,
      'rouge-l': 0
    }
    static_message_bleu = {
      'bleu-1': 0,
      'bleu-2': 0,
      'bleu-3': 0,
      'bleu-4': 0,
      'bleu-A': 0
    }
    rouge = Rouge()

    data = read_json_sample(input_file_path)
    for row in data:
        data_num += 1

        '''Get ground truth'''
        ground_truth = row["metadata"]
        message_gth = get_gro_mes(ground_truth["statement"])
        pos_gth = ground_truth['position'].split('-')[0]
        level_gth = ground_truth['level']
        vars_gth = ground_truth['vars']
        static_message_gth, x = extract_static_and_vars(message_gth)

        '''Get predictions'''
        pos_pred, level_pred, message_pred = get_logging_greedy(row['response'])
        if pos_pred == None:
           continue

        validate_num += 1
        static_message_pred, vars_pred = extract_static_and_vars(message_pred)

        if pos_gth == pos_pred:
            pos_count += 1

        if abs(int(pos_gth) - int(pos_pred)) <= 1:
          pos_related_count += 1

        if level_gth == level_pred:
            level_count += 1
        
        if message_gth.replace(' ', '') == message_pred.replace(' ', ''):
            message_count += 1
            static_message_bleu['bleu-A'] += 100
            static_message_bleu['bleu-1'] += 100
            static_message_bleu['bleu-2'] += 100
            static_message_bleu['bleu-3'] += 100
            static_message_bleu['bleu-4'] += 100
            static_message_rouge['rouge-1'] += 1
            static_message_rouge['rouge-2'] += 1
            static_message_rouge['rouge-l'] += 1
        else:
            # print("Ground truth:", static_message_gth)
            # print("Prediction:", static_message_pred)
            # static_message_pred = ' '.join(wordninja.split(static_message_pred))
            bleu = sentence_bleu(static_message_gth, [static_message_pred], smooth_method='none')
            bleu1_score = bleu.precisions[0]
            bleu2_score = bleu.precisions[1]
            bleu3_score = bleu.precisions[2]
            bleu4_score = bleu.precisions[3]
            bleuA_score = bleu.score
            static_message_bleu['bleu-1'] += bleu1_score
            static_message_bleu['bleu-2'] += bleu2_score
            static_message_bleu['bleu-3'] += bleu3_score
            static_message_bleu['bleu-4'] += bleu4_score
            static_message_bleu['bleu-A'] += bleuA_score

        rouge_score = rouge.get_scores(static_message_gth if static_message_gth != '' else ' ', static_message_pred if static_message_pred != '' else ' ', avg=True, ignore_empty=True)
        static_message_rouge['rouge-1'] += rouge_score['rouge-1']['f']
        static_message_rouge['rouge-2'] += rouge_score['rouge-2']['f']
        static_message_rouge['rouge-l'] += rouge_score['rouge-l']['f']
        # Calculate variables accuracy
        if check_vars_accuracy(vars_pred, vars_gth):
            vars_accuracy_count += 1
        
        prediction_level = cat_dict[level_pred] if level_pred in cat_dict else 100
        ground_truth_level = cat_dict[level_gth]
        # 计算level距离
        level_distance = min(abs(prediction_level - ground_truth_level), 5)
        if level_distance in level_distance_dict:
            level_distance_dict[level_distance] += 1
        else:
            level_distance_dict[level_distance] = 1

    metrics = {
      "# of Tools": tool_name,
      "PA": round(pos_count / data_num * 100, 3),
      "PRA": round(pos_related_count / data_num * 100, 3),
      "LA": round(level_count / data_num * 100, 3),
      "Level Distance": round(sum([k*v for k, v in level_distance_dict.items()])/data_num, 4),
      "MA": round(message_count / data_num * 100, 3),
      "VA": round(vars_accuracy_count / data_num * 100, 3),
      "BLEU-A/1/2/3/4": f"{round(static_message_bleu['bleu-A'] / data_num, 3)}/{round(static_message_bleu['bleu-1'] / data_num, 3)}/{round(static_message_bleu['bleu-2'] / data_num, 3)}/{round(static_message_bleu['bleu-3'] / data_num, 3)}/{round(static_message_bleu['bleu-4'] / data_num, 3)}",
      "ROUGE-1/2/l": f"{round(static_message_rouge['rouge-1']*100 / data_num, 3)}/{round(static_message_rouge['rouge-2']*100 / data_num, 3)}/{round(static_message_rouge['rouge-l']*100 / data_num, 3)}",
      "Validate": f"{validate_num}/{data_num}"
    }
    
    # Print markdown format
    markdown_str = "\nMarkdown format:\n"
    markdown_str += "| " + " | ".join(metrics.keys()) + " |\n"
    markdown_str += "| " + " | ".join("-" * len(key) for key in metrics.keys()) + " |\n"
    markdown_str += "| " + " | ".join(str(value) for value in metrics.values()) + " |"
    
    # 生成表格格式结果
    table_str = "\nPretty table format:\n"
    headers = list(metrics.keys())
    data = [list(metrics.values())]
    table_str += tabulate(data, headers=headers, tablefmt='grid')

    return metrics, markdown_str, table_str

def evaluate(folder_path,tool_name):
    metrics, markdown_str, table_str = evaluation_greedy(folder_path, tool_name)
    print(markdown_str)
    print(table_str)

def evaluate_all_projects(folder_path):
    """
    评估指定文件夹下所有json文件的结果
    Args:
        folder_path: json文件所在文件夹路径
    """
    import os
    
    # 存储所有工具的评估结果
    all_metrics = []
    
    # 遍历文件夹下所有json文件
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            # 从文件名中提取工具名称
            tool_name = filename.split('_')[0]
            file_path = os.path.join(folder_path, filename)
            
            # 评估单个工具
            metrics, _, _ = evaluation_greedy(file_path, tool_name)
            all_metrics.append(list(metrics.values()))
    
    # 生成汇总表格
    if all_metrics:
        headers = list(metrics.keys())
        table_str = "\n所有工具评估结果:\n"
        table_str += tabulate(all_metrics, headers=headers, tablefmt='grid')
        print(table_str)
        
        # 生成markdown格式
        markdown_str = "\nMarkdown格式:\n"
        markdown_str += "| " + " | ".join(headers) + " |\n"
        markdown_str += "| " + " | ".join("-" * len(key) for key in headers) + " |\n"
        for metric in all_metrics:
            markdown_str += "| " + " | ".join(str(value) for value in metric) + " |\n"
        print(markdown_str)
    else:
        print("未找到json文件")



if __name__ == "__main__":
  # evaluate_all_projects('../static_data/unilog/res/cleaned_res/deepseek_base/len_discuss')
  evaluate('../static_data/unilog/res/cleaned_res/warmup_cl/static_test_data_warmup_cl_cleaned.json', 'unilog_all')