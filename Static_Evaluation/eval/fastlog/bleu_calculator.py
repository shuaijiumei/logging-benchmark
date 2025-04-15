from nltk.translate.bleu_score import corpus_bleu
from nltk.translate.bleu_score import sentence_bleu

from sacrebleu import sentence_bleu


def my_sentence_bleu(candidate_list, reference_list):
    bleu1_sum = bleu2_sum = bleu3_sum = bleu4_sum = bleuA_sum = 0

    for (ref, cand) in zip(reference_list, candidate_list):

        tokens_real = ref.split(' ')
        tokens_pred = cand.split(' ')

        if cand == '':
            bleu1_score = bleu2_score = bleu3_score = bleu4_score = bleuA_score = 0

        else:
            # bleu1_score = sentence_bleu([tokens_real], tokens_pred, weights=(1.0, 0.0, 0.0, 0.0))
            # bleu2_score = sentence_bleu([tokens_real], tokens_pred, weights=(0.0, 1.0, 0.0, 0.0))
            # bleu3_score = sentence_bleu([tokens_real], tokens_pred, weights=(0.0, 0.0, 1.0, 0.0))
            # bleu4_score = sentence_bleu([tokens_real], tokens_pred, weights=(0.0, 0.0, 0.0, 1.0))
            # bleuA_score = sentence_bleu([tokens_real], tokens_pred, weights=(0.25, 0.25, 0.25, 0.25))
            bleu = sentence_bleu(ref, [cand], smooth_method='none')
            bleu1_score = bleu.precisions[0]
            bleu2_score = bleu.precisions[1]
            bleu3_score = bleu.precisions[2]
            bleu4_score = bleu.precisions[3]
            bleuA_score = bleu.score

        bleu1_sum += bleu1_score
        bleu2_sum += bleu2_score
        bleu3_sum += bleu3_score
        bleu4_sum += bleu4_score
        bleuA_sum += bleuA_score

    output = 'BLEU_[A-1-2-3-4]: {}/{}/{}/{}/{}'.format(
        round(bleuA_sum / len(reference_list), 3),
        round(bleu1_sum / len(reference_list), 3),
        round(bleu2_sum / len(reference_list), 3),
        round(bleu3_sum / len(reference_list), 3),
        round(bleu4_sum / len(reference_list), 3)
    )
    print(output)


def my_corpus_bleu(preds, refs, verbose=False):
    refs = [[ref.strip().split()] for ref in refs]
    preds = [pred.strip().split() for pred in preds]
    print(preds[0])
    print(refs[0])

    Ba = corpus_bleu(refs, preds)

    def r(B):
        return round(B * 100, 4)

    if verbose:
        B1 = corpus_bleu(refs, preds, weights=(1, 0, 0, 0))
        B2 = corpus_bleu(refs, preds, weights=(0, 1, 0, 0))
        B3 = corpus_bleu(refs, preds, weights=(0, 0, 1, 0))
        B4 = corpus_bleu(refs, preds, weights=(0, 0, 0, 1))
        print('BLEU: {:.4f}\tB1: {:.4f}\tB2: {:.4f}\tB3: {:.4f}\tB4: {:.4f}'.format(r(Ba), r(B1), r(B2), r(B3), r(B4)))

    return Ba



