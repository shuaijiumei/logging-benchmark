import argparse
import pandas as pd
import re
from sacrebleu import sentence_bleu



def get_gro_mes(sample):
    log = sample
    log = log.strip()
    res = re.search(r'[.](off)?(fatal)?(error)?(warn)?(info)?(debug)?(trace)?(all)?[(]', log)
    if res is not None:
        level = log[res.span()[0] + 1: res.span()[1] - 1].strip()
        pattern = re.compile('%s\((.+)\)' % level)
        result = pattern.findall(log)
        if result == []:
            message = ""
        else:
            message = result[0]
    else:
        level, message = "", ""
    return message.lower()

def get_logging_greedy(sample):
    # 正则匹配 <linex> x 是任意数字,只取出其中的数字
    search_result = re.search(r'<line(\d+)>', sample)
    pos = search_result.group(1) if search_result else None
    if pos is None:
        return None, None, None

    log = sample.replace('<line%s>' % pos, ' ')

    log = log.strip()
    res = re.search(r'[.](off)?(fatal)?(error)?(warn)?(info)?(debug)?(trace)?(all)?[(]', log)
    if res is not None:
        level = log[res.span()[0] + 1: res.span()[1] - 1].strip()
        pattern = re.compile('%s\((.+)\)' % level)
        result = pattern.findall(log)
        if result == []:
            message = ""
        else:
            message = result[0]
    else:
        level, message = "", ""
    return pos.lower(), level.lower(), message.lower()

def extract_min_expression(vars):
    if vars == None or vars == '':
        return []
    pattern_plus = re.compile(r'\b[a-zA-Z]+\s?\+\s?[a-zA-Z]+\b')
    pattern_minus = re.compile(r'\b[a-zA-Z]+\s?\-\s?[a-zA-Z]+\b')
    pattern_multi = re.compile(r'\b[a-zA-Z]+\s?\*\s?[a-zA-Z]+\b')
    pattern_div = re.compile(r'\b[a-zA-Z]+\s?/\s?[a-zA-Z]+\b')
    pattern_mod = re.compile(r'\b[a-zA-Z]+\s?%\s?[a-zA-Z]+\b')
    pattern_equal = re.compile(r'\b[a-zA-Z]+\s?==\s?[a-zA-Z]+\b')
    pattern_not_equal = re.compile(r'\b[a-zA-Z]+\s?!=\s?[a-zA-Z]+\b')
    pattern_condition = re.compile(r'\b[a-zA-Z]+\s?\?\s?[a-zA-Z]+\s?:\s?[a-zA-Z]+\b')

    # 从 vars 中找到上诉所有的表达式
    min_expression = []
    min_expression.extend(pattern_plus.findall(vars))
    min_expression.extend(pattern_minus.findall(vars))
    min_expression.extend(pattern_multi.findall(vars))
    min_expression.extend(pattern_div.findall(vars))
    min_expression.extend(pattern_mod.findall(vars))
    min_expression.extend(pattern_equal.findall(vars))
    min_expression.extend(pattern_not_equal.findall(vars))
    min_expression.extend(pattern_condition.findall(vars))
    
    # 遍历 min_expression，消除掉 vars 中的表达式，剩下的就是单独的变量
    for exp in min_expression:
        vars = vars.replace(exp, "")
    vars = vars.split(' ')
    # 去除掉除包含字母的所有元素
    vars = [var for var in vars if re.search(r'[a-zA-Z]', var)]

    # 将 vars 和 min_expression 合并
    vars.extend(min_expression)
    return vars

def extract_static_and_vars(message):
    static_parts = re.findall(r'"([^"]*)"', message)
    static_message = ' '.join(static_parts)
    vars_parts = re.sub(r'"[^"]*"', '', message)
    vars_parts = extract_min_expression(vars_parts)

    return static_message, vars_parts

def check_vars_accuracy(vars_pred, vars_gth):
    missing_vars = [var for var in vars_gth if var not in vars_pred]
    return len(missing_vars) == 0 and len(vars_pred) == len(vars_gth)

def evaluation_greedy(input_file_path):
    pos_count, level_count, message_count, static_message_bleu, vars_accuracy_count = 0, 0, 0, 0, 0
    data_num = 0

    df_raw = pd.read_csv(input_file_path, sep='\t')
    for i, row in df_raw.iterrows():
        data_num += 1

        '''Get ground truth'''
        message_gth = get_gro_mes(row["statement"])
        pos_gth = row['position'].split('-')[0]
        level_gth = row['level']
        vars_gth = str(row['vars'])
        static_message_gth, x = extract_static_and_vars(message_gth)

        '''Get predictions'''
        pos_pred, level_pred, message_pred = get_logging_greedy(row['predict'])
        static_message_pred, vars_pred = extract_static_and_vars(message_pred)

        if pos_gth == pos_pred:
            pos_count += 1
        if level_gth == level_pred:
            level_count += 1
        
        if message_gth == message_pred:
            message_count += 1
            static_message_bleu += 100
        else:
            static_message_bleu += sentence_bleu(static_message_gth, [static_message_pred], 'none').score

        # Calculate variables accuracy
        if check_vars_accuracy(vars_pred, vars_gth):
            vars_accuracy_count += 1

    # data_num = 42669
    metrics = {
        "# of Samples": data_num,
        "Position Accuracy (PA)": round(pos_count / data_num * 100, 3),
        "Level Accuracy (LA)": round(level_count / data_num * 100, 3),
        "Message Accuracy (MA)": round(message_count / data_num * 100, 3),
        "Static Text Accuracy BLEU (STA)": round(static_message_bleu / data_num, 3),
        "Variables Accuracy (VA)": round(vars_accuracy_count / data_num * 100, 3)
    }
    
    print("| Metric | Value |")
    print("|--------|-------|")
    for metric, value in metrics.items():
        print(f"| {metric} | {value} |")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in_dir', default="./res/project_csvs/", type=str)
    args = parser.parse_args()

    import os
    for file_name in os.listdir(args.in_dir):
        if file_name.endswith('.tsv'):
            file_path = os.path.join(args.in_dir, file_name)
            print(f"Evaluating file: {file_path}")
            evaluation_greedy(file_path)
