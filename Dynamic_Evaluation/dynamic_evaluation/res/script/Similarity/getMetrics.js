const evaluate_model = "fastlog";

const evaluation_res = require(`../../data/${evaluate_model}/common_evaluation.json`);

const perfect_list = require(`../../data/${evaluate_model}/perfect_list.json`);

const condition_score = true;

const total_length = 2238;

const valid_length_map = {
  leonid_m: 560,
  leonid: 368,
  fastlog: 1788,
  unilog: 1527,
  lance: 1104,
};

const r = (x) => {
  return Math.round(x * 100 * 10000) / 10000;
};

const getMetrics = (data) => {
  const valid_length = valid_length_map[evaluate_model];

  let total_rouge_score = {
    "rouge-1": {
      recall: 0,
      precision: 0,
      fmeasure: 0,
    },
    "rouge-2": {
      recall: 0,
      precision: 0,
      fmeasure: 0,
    },
    "rouge-l": {
      recall: 0,
      precision: 0,
      fmeasure: 0,
    },
  };
  let total_bleu_score = {
    bleu: 0,
    bleu_1: 0,
    bleu_2: 0,
    bleu_3: 0,
    bleu_4: 0,
  };

  let cosine_similarity = 0;

  data.forEach((item) => {
    if (item.success === true) {
      total_rouge_score["rouge-1"].recall += item.rouge_score["rouge-1"].recall;
      total_rouge_score["rouge-1"].precision +=
        item.rouge_score["rouge-1"].precision;
      total_rouge_score["rouge-1"].fmeasure +=
        item.rouge_score["rouge-1"].fmeasure;

      total_rouge_score["rouge-2"].recall += item.rouge_score["rouge-2"].recall;
      total_rouge_score["rouge-2"].precision +=
        item.rouge_score["rouge-2"].precision;
      total_rouge_score["rouge-2"].fmeasure +=
        item.rouge_score["rouge-2"].fmeasure;

      total_rouge_score["rouge-l"].recall += item.rouge_score["rouge-l"].recall;
      total_rouge_score["rouge-l"].precision +=
        item.rouge_score["rouge-l"].precision;
      total_rouge_score["rouge-l"].fmeasure +=
        item.rouge_score["rouge-l"].fmeasure;

      total_bleu_score["bleu"] += item.bleu_score["bleu"];
      total_bleu_score["bleu_1"] += item.bleu_score["bleu_1"];
      total_bleu_score["bleu_2"] += item.bleu_score["bleu_2"];
      total_bleu_score["bleu_3"] += item.bleu_score["bleu_3"];
      total_bleu_score["bleu_4"] += item.bleu_score["bleu_4"];

      cosine_similarity += item.cosine_similarity;
    }
  });

  const perfect_matches = perfect_list.length;

  const average_rouge_score = {
    "rouge-1": {
      recall: r(
        (total_rouge_score["rouge-1"].recall + perfect_matches) / valid_length
      ),
      precision: r(
        (total_rouge_score["rouge-1"].precision + perfect_matches) /
          valid_length
      ),
      fmeasure: r(
        (total_rouge_score["rouge-1"].fmeasure + perfect_matches) / valid_length
      ),
    },
    "rouge-2": {
      recall: r(
        (total_rouge_score["rouge-2"].recall + perfect_matches) / valid_length
      ),
      precision: r(
        (total_rouge_score["rouge-2"].precision + perfect_matches) /
          valid_length
      ),
      fmeasure: r(
        (total_rouge_score["rouge-2"].fmeasure + perfect_matches) / valid_length
      ),
    },
    "rouge-l": {
      recall: r(
        (total_rouge_score["rouge-l"].recall + perfect_matches) / valid_length
      ),
      precision: r(
        (total_rouge_score["rouge-l"].precision + perfect_matches) /
          valid_length
      ),
      fmeasure: r(
        (total_rouge_score["rouge-l"].fmeasure + perfect_matches) / valid_length
      ),
    },
  };

  const average_bleu_score = {
    bleu: (total_bleu_score["bleu"] + perfect_matches * 100) / valid_length,
    "bleu-1":
      (total_bleu_score["bleu_1"] + perfect_matches * 100) / valid_length,
    "bleu-2":
      (total_bleu_score["bleu_2"] + perfect_matches * 100) / valid_length,
    "bleu-3":
      (total_bleu_score["bleu_3"] + perfect_matches * 100) / valid_length,
    "bleu-4":
      (total_bleu_score["bleu_4"] + perfect_matches * 100) / valid_length,
  };

  /* 
  Cosine Similarity:
    FastLog: 0.21318878566487132
    UniLog: 0.17375493138597314
    LANCE: 0.09934707395499956
    Leonid: 0.04446139570894331
    Leonid_M: 0.07188292130619969
  Conditional Cosine Similarity:
    FastLog: 0.266843681385896
    UniLog: 0.25465850454604316
    LANCE: 0.2013937966587763
    Leonid: 0.27039294455601937
    Leonid_M: 0.28727496050584805
  */
  const average_cosine_similarity =
    (cosine_similarity + perfect_matches) /
    (condition_score ? valid_length : total_length);

  console.log(`average_rouge_score: ${JSON.stringify(average_rouge_score)}`);
  console.log(`average_bleu_score: ${JSON.stringify(average_bleu_score)}`);
  console.log(`average_cosine_similarity: ${average_cosine_similarity}`);
};

getMetrics(evaluation_res);
