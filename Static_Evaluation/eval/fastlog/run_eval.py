import pandas as pd
import re

from bleu_calculator import my_corpus_bleu, my_sentence_bleu
from rouge_calculator import cal_rouge

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
    
    for exp in min_expression:
        vars = vars.replace(exp, "")
    vars = vars.split(' ')
    vars = [var for var in vars if re.search(r'[a-zA-Z]', var)]

    vars.extend(min_expression)
    return vars


def cal_position_metrics(prediction_file, label_file):
    print("Evaluate log position...")
    correct_class = 1
    predictions = pd.read_csv(prediction_file)["Position"]
    target_labels = pd.read_csv(label_file)["Label"]
    targets = target_labels.apply(lambda x: [int(num) for num in x.split()].index(correct_class))
    data = pd.DataFrame()
    data["prediction"] = predictions
    data["target"] = targets
    data["match"] = data["prediction"] == data["target"]
    print("Accuracy: {}     Correct: {}     Total: {}".format(100 * len(data[data["match"] == True]) / len(data),
                                                              len(data[data["match"] == True]), len(data)))


def cal_level_metrics(predict_file, label_file, position_predict_file, position_label_file):
    print("Evaluate log level...")
    cat_dict = {'trace': 0, 'debug': 1, 'info': 2, 'warn': 3, 'error': 4, 'fatal': 5}
    predictions = pd.read_csv(predict_file)["Level"]
    targets = pd.read_csv(label_file)["Level"]
    logSta = pd.read_csv(label_file)["LogStatement"]
    targets = targets.replace(cat_dict)
    targets = targets.apply(lambda x: x if x in range(6) else 0)
    target_list = targets.tolist()
    predictions = predictions.apply(lambda x: int(x) if int(x) in range(6) else 100)
    level_dis = {}
    for i in range(len(target_list)):
        dis = min(abs(target_list[i] - int(predictions[i])), 6)
        if dis in level_dis:
            level_dis[dis] += 1
        else:
            level_dis[dis] = 1
    data_num = len(target_list)
    print("average level distance: ", sum([(6-k)*v for k, v in level_dis.items()])/data_num)
    print("average level shift rate: ", sum([(6-k)*v for k, v in level_dis.items()])/data_num/6)


    data = pd.DataFrame()
    data["prediction"] = predictions
    data["target"] = targets

    data["position_prediction"] = pd.read_csv(position_predict_file)["Position"]
    data["position_target"] = pd.read_csv(position_label_file)["Label"].apply(lambda x: [int(num) for num in x.split()].index(1))

    condition_level_acc = 0
    for i in range(len(data)):
        if data["position_prediction"][i] == data["position_target"][i] and data["prediction"][i] == data["target"][i]:
            condition_level_acc += 1
    print("Condition Level Accuracy: {}     Correct: {}     Total: {}".format(100 * condition_level_acc / len(data),
                                                            condition_level_acc, len(data)) )

    data["match"] = data["prediction"] == data["target"]
    print("Accuracy: {}     Correct: {}     Total: {}".format(100 * len(data[data["match"] == True]) / len(data),
                                                            len(data[data["match"] == True]), len(data)))

def cal_condition_message_metrics(data):
    condition_message_acc = 0
    for i in range(len(data)):
        if data["position_prediction"][i] == data["position_target"][i] and data["match"][i]:
            condition_message_acc += 1
    print("Condition Message Accuracy: {}     Correct: {}     Total: {}".format(100 * condition_message_acc / len(data),
                                                            condition_message_acc, len(data)) )

def cal_dynamic_part_accuracy(data, predictions, targets):
    dynamic_part_acc = 0
    for i in range(len(data)):
        if predictions[i] == targets[i]:
            dynamic_part_acc += 1
            # print(predictions[i], "=======", targets[i])
    print("Dynamic Part Accuracy: {}     Correct: {}     Total: {}".format(100 * dynamic_part_acc / len(data),
                                                            dynamic_part_acc, len(data)) )


def cal_message_metrics(prediction_file, label_file,position_predict_file, position_label_file):
    print("Evaluate log message...")
    predictions = pd.read_csv(prediction_file)["Message"]
    predictions.fillna(" ", inplace=True)
    targets = pd.read_csv(label_file)["Message"].apply(lambda x: re.findall(r'"([^"]*)"', x))
    vars_parts = pd.read_csv(prediction_file)["Message"].apply(lambda x: extract_min_expression(re.sub(r'"[^"]*"', '', x)))
    vars_parts_target = pd.read_csv(label_file)["VarList"].apply(lambda x: str(x).split(',') if ',' in str(x) else ([] if str(x).strip() == '' else [x]))

    try:
        data = pd.DataFrame()
        data["position_prediction"] = pd.read_csv(position_predict_file)["Position"]
        data["position_target"] = pd.read_csv(position_label_file)["Label"].apply(lambda x: [int(num) for num in x.split()].index(1))
        data["prediction"] = predictions.apply(lambda x: x.replace(' ', ''))
        data["target"] = pd.read_csv(label_file)["Message"].apply(lambda x: str(x).replace(' ', ''))
        data["match"] = data["prediction"].apply(lambda x: x[1:-1].strip())== data["target"]

        static_predictions = predictions.apply(lambda x: re.findall(r'"([^"]*)"', x))
        cal_dynamic_part_accuracy(data, vars_parts, vars_parts_target)

        print(targets.head())

    except Exception as e:
        print(e)
    print("Accuracy: {}     Correct: {}     Total: {}".format(100 * len(data[data["match"] == True]) / len(data),
                                                              len(data[data["match"] == True]), len(data)))

    my_sentence_bleu([str(i) for i in static_predictions.to_list()], [str(i) for i in targets.tolist()])
    my_corpus_bleu([str(i) for i in static_predictions.to_list()], [str(i) for i in targets.tolist()], True)
    cal_rouge([str(i) for i in static_predictions.to_list()], [str(i) for i in targets.tolist()])


def cal_all_metrics(position_prediction_file, position_label_file, logsta_prediction_file, logsta_label_file):
    print("Evaluate all log aspects...")
    correct_class = 1
    position_predictions = pd.read_csv(position_prediction_file)["Position"]
    position_target_labels = pd.read_csv(position_label_file)["Label"]
    position_targets = position_target_labels.apply(lambda x: [int(num) for num in x.split()].index(correct_class))

    logsta_predictions = pd.read_csv(logsta_prediction_file)["LogStatement"]
    logsta_targets = pd.read_csv(logsta_label_file)["LogStatement"].apply(lambda x: x+' ;')
    logsta_predictions.fillna(" ", inplace=True)
    logsta_predictions = logsta_predictions.apply(lambda x: x.replace(' ', ''))
    logsta_targets = logsta_targets.apply(lambda x: x.replace(' ', ''))

    data = pd.DataFrame()
    data["position_prediction"] = position_predictions
    data["position_target"] = position_targets
    data["logsta_prediction"] = logsta_predictions
    data["logsta_target"] = logsta_targets
    data["match"] = (data["position_prediction"] == data["position_target"]) & (
                data["logsta_prediction"] == data["logsta_target"])
    print("Accuracy: {}     Correct: {}     Total: {}".format(100 * len(data[data["match"] == True]) / len(data),
                                                              len(data[data["match"] == True]), len(data)))


if __name__ == '__main__':
    position_prediction_file = '//YOU PATH// /positions_test.csv"
    position_label_file = "//YOU PATH// /stage1-input.csv"
    logsta_prediction_file = "//YOU PATH// /statements_beam_search.csv"
    logsta_label_file = "//YOU PATH// /stage2-input.csv"

    print("-" * 100)
    cal_position_metrics(position_prediction_file, position_label_file)
    cal_level_metrics(logsta_prediction_file, logsta_label_file, position_prediction_file, position_label_file)
    cal_message_metrics(logsta_prediction_file, logsta_label_file, position_prediction_file, position_label_file)
    cal_all_metrics(position_prediction_file, position_label_file, logsta_prediction_file, logsta_label_file)