# -*- coding: utf-8 -*-

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
from tqdm import tqdm
from sacrebleu import sentence_bleu
from rouge_score import rouge_scorer
import os

def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def read_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def get_true_prediction_file(item):
    return read_txt(item['file_location'])

def calculate_rouge_score(reference, candidate):
    scorer = rouge_scorer.RougeScorer(
        ['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(reference, candidate)
    return {
        'rouge-1': {
            'recall': scores['rouge1'].recall,
            'precision': scores['rouge1'].precision,
            'fmeasure': scores['rouge1'].fmeasure
        },
        'rouge-2': {
            'recall': scores['rouge2'].recall,
            'precision': scores['rouge2'].precision,
            'fmeasure': scores['rouge2'].fmeasure
        },
        'rouge-l': {
            'recall': scores['rougeL'].recall,
            'precision': scores['rougeL'].precision,
            'fmeasure': scores['rougeL'].fmeasure
        }
    }


def calculate_cosine_similarity(text1, text2):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return cosine_sim[0][0]


def calculate_bleu_score(tokens_real, tokens_pred, bleu_score_record):
    bleu = sentence_bleu(tokens_real, [tokens_pred], smooth_method='none')

    bleu_score_record['total_bleu_score'] += bleu.score
    bleu_score_record['total_bleu1_score'] += bleu.precisions[0]
    bleu_score_record['total_bleu2_score'] += bleu.precisions[1]
    bleu_score_record['total_bleu3_score'] += bleu.precisions[2]
    bleu_score_record['total_bleu4_score'] += bleu.precisions[3]

    return {
        'bleu': bleu.score,
        'bleu_1': bleu.precisions[0],
        'bleu_2': bleu.precisions[1],
        'bleu_3': bleu.precisions[2],
        'bleu_4': bleu.precisions[3]
    }


def read_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        # 读取文件内容，划分为数组
        res = []
        content = f.read().split('\n')
        for item in content:
            res.append(item.split('[SUPER TAG]').pop())
        # 将数组转换为字符串返回
        return ''.join(res)


def r(x):
    return round(x * 100, 4)


def get_common_case(compare_data, baseline_data):
    common_case = []
    
    for item in compare_data:
        if item['execute_success']:
            baseline_item = next((b for b in baseline_data if b['uuid'] == item['uuid']), None)
            if baseline_item:
                baseline_item_size = baseline_item['file_size']
                item_size = item['file_size']
                
                if baseline_item_size != 0 and item_size != 0:
                    common_case.append({
                        'uuid': item['uuid'],
                        'baseline_size': baseline_item_size,
                        'compare_size': item_size
                    })
                if baseline_item_size == 0 and item_size == 0:
                    common_case.append({
                        'uuid': item['uuid'],
                        'baseline_size': baseline_item_size,
                        'compare_size': item_size
                    })
    
    return common_case

def evaluate_model_results(evaluate_model_name, baseline_data):
    prediction_data = read_jsonl(f'./data/res/{evaluate_model_name}.jsonl')
    common_case = get_common_case(prediction_data, baseline_data)

    perfect_list = []
    common_evaluate_list = []
    bleu_score_record = {
        'total_bleu_score': 0,
        'total_bleu1_score': 0,
        'total_bleu2_score': 0,
        'total_bleu3_score': 0,
        'total_bleu4_score': 0
    }

    for d in tqdm(common_case):
        if d['baseline_size'] == d['compare_size'] == 0:
            perfect_list.append(d)
            continue
        if d['baseline_size'] > 50000 or d['compare_size'] > 50000:
            continue

        uuid = d['uuid']
        baseline_item = [
            item for item in baseline_data if item['uuid'] == uuid].pop()
        prediction_item = [
            item for item in prediction_data if item['uuid'] == uuid].pop()

        baseline_item_text = get_true_prediction_file(baseline_item)
        prediction_item_text = get_true_prediction_file(prediction_item)

        # bleu_score
        d['bleu_score'] = calculate_bleu_score(
            baseline_item_text, prediction_item_text, bleu_score_record)
        # rouge_score
        d['rouge_score'] = calculate_rouge_score(
            baseline_item_text, prediction_item_text)
        d['cosine_similarity'] = calculate_cosine_similarity(
            baseline_item_text, prediction_item_text)
        d['success'] = True
        common_evaluate_list.append(d)

    # 保存评估结果到 data/eval_res/evaluate_model_name.jsonl
    if not os.path.exists('./data/eval_res'):
        os.makedirs('./data/eval_res')
    if not os.path.exists(f'./data/eval_res/{evaluate_model_name}'):
        os.makedirs(f'./data/eval_res/{evaluate_model_name}')
    with open(f'./data/eval_res/{evaluate_model_name}/eval_res.json', 'w', encoding='utf-8') as f:
        json.dump(common_evaluate_list, f, ensure_ascii=False, indent=2)
    with open(f'./data/eval_res/{evaluate_model_name}/perfect_list.json', 'w', encoding='utf-8') as f:
        json.dump(perfect_list, f, ensure_ascii=False, indent=2)

def main():
    # choose the evaluate model name unilog, unilog_deepseek, fastlog, leonid, leonid_m, lance
    evaluate_model_name_list = ['unilog', 'unilog_deepseek', 'fastlog', 'leonid', 'leonid_m', 'lance']
    baseline_data = read_jsonl(f'./data/res/baseline.jsonl')

    for evaluate_model_name in evaluate_model_name_list:
        evaluate_model_results(evaluate_model_name, baseline_data)

if __name__ == '__main__':
    main()