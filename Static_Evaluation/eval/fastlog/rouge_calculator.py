from rouge import Rouge


def r(x):
    return round(x * 100, 4)


def cal_rouge(hypotheses, references):
    rouge = Rouge()
    avg_score = rouge.get_scores(hypotheses, references, avg=True, ignore_empty=True)
    print('rouge-1: {:.4}\t\trouge-2: {:.4}\t\trouge-l: {:.4}'.format(r(avg_score['rouge-1']['f']),
                                                                      r(avg_score['rouge-2']['f']),
                                                                      r(avg_score['rouge-l']['f'])))