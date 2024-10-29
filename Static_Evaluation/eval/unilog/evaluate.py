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
    pos = re.search(r'<line(\d+)>', sample).group(1)

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

    min_expression = []
    min_expression.extend(pattern_plus.findall(vars))
    min_expression.extend(pattern_minus.findall(vars))
    min_expression.extend(pattern_multi.findall(vars))
    min_expression.extend(pattern_div.findall(vars))
    min_expression.extend(pattern_mod.findall(vars))
    min_expression.extend(pattern_equal.findall(vars))
    min_expression.extend(pattern_not_equal.findall(vars))
    min_expression.extend(pattern_condition.findall(vars))
    
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
    return len(missing_vars) == 0

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

        if int(pos_gth) == int(pos_pred):
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

    # data_num = 42224
    print("# of Samples: ", data_num)
    print("Position Accuracy (PA): ", round(pos_count / data_num *100, 3))
    print("Level Accuracy (LA): ", round(level_count / data_num *100, 3))
    print("Message Accuracy (MA): ", round(message_count / data_num *100, 3))
    print("Static Text Accuracy BLEU (STA): ", round(static_message_bleu / data_num, 3))
    print("Variables Accuracy (VA): ", round(vars_accuracy_count / data_num * 100, 3))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser.add_argument('--in_file', default="./staticData_unilog_prediction.tsv", type=str)
    parser.add_argument('--in_file', default="../../data/data/unilog/staticData_unilog_prediction.tsv", type=str)
    # parser.add_argument('--in_file', default="./prediction/unilog/test.tsv", type=str)
    args = parser.parse_args()

    evaluation_greedy(args.in_file)
