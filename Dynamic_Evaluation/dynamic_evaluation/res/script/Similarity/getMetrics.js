const fs = require("fs");

// 所有需要评估的模型
const ALL_MODELS = [
  "leonid_m",
  "leonid",
  "fastlog",
  "unilog",
  "lance",
  "unilog_deepseek",
];

const r = (x) => Math.round(x * 100 * 10000) / 10000;

function evaluateModel(model_name) {
  const evaluation_res = require(`../data/${model_name}/common_evaluation.json`);
  const perfect_list = require(`../data/${model_name}/perfect_list.json`);
  const valid_length = 2238;

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

  evaluation_res.forEach((item) => {
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

  const average_cosine_similarity =
    (cosine_similarity + perfect_matches) / valid_length;

  return {
    model: model_name,
    rouge: {
      rouge1: average_rouge_score["rouge-1"].fmeasure.toFixed(3),
      rouge2: average_rouge_score["rouge-2"].fmeasure.toFixed(3),
      rougeL: average_rouge_score["rouge-l"].fmeasure.toFixed(3),
    },
    bleu: {
      bleu: average_bleu_score["bleu"].toFixed(3),
      bleu1: average_bleu_score["bleu-1"].toFixed(3),
      bleu2: average_bleu_score["bleu-2"].toFixed(3),
      bleu3: average_bleu_score["bleu-3"].toFixed(3),
      bleu4: average_bleu_score["bleu-4"].toFixed(3),
    },
    cosine: average_cosine_similarity.toFixed(3),
  };
}

function generateTable(results) {
  // 按 Cosine 值排序
  const sortedResults = [...results].sort(
    (a, b) => parseFloat(b.cosine) - parseFloat(a.cosine)
  );

  // 生成控制台表格
  console.table(
    sortedResults.map((r) => ({
      Model: r.model,
      Cosine: r.cosine,
      BLEU: r.bleu.bleu,
      "BLEU-1": r.bleu.bleu1,
      "BLEU-4": r.bleu.bleu4,
      "ROUGE-1": r.rouge.rouge1,
      "ROUGE-L": r.rouge.rougeL,
    }))
  );
}

function generateMarkdown(results) {
  // 按 Cosine 值排序
  const sortedResults = [...results].sort(
    (a, b) => parseFloat(b.cosine) - parseFloat(a.cosine)
  );

  let md = `
## 模型评估结果

| Model | Cosine | BLEU | BLEU-1 | BLEU-4 | ROUGE-1 | ROUGE-L |
|-------|---------|------|---------|---------|----------|----------|
`;

  sortedResults.forEach((r) => {
    md += `| ${r.model} | ${r.cosine} | ${r.bleu.bleu} | ${r.bleu.bleu1} | ${r.bleu.bleu4} | ${r.rouge.rouge1} | ${r.rouge.rougeL} |\n`;
  });

  return md;
}

function evaluateAll() {
  const results = ALL_MODELS.map((model) => evaluateModel(model));

  // 输出表格形式
  console.log("\n=== 评估结果表格 ===");
  generateTable(results);

  // 输出 Markdown
  console.log("\n=== Markdown 格式 ===");
  console.log(generateMarkdown(results));

  // 保存结果到文件
  fs.writeFileSync("evaluation_results.md", generateMarkdown(results), "utf8");

  return results;
}

// 命令行参数处理
const args = process.argv.slice(2);
if (args.length > 0) {
  // 评估单个模型
  const model = args[0];
  if (!ALL_MODELS.includes(model)) {
    console.error(`错误：未知的模型 "${model}"`);
    console.log("可用的模型：", ALL_MODELS.join(", "));
    process.exit(1);
  }

  const result = evaluateModel(model);
  console.log("\n=== 单模型评估结果 ===");
  console.log(`模型：${model}`);
  console.log("\nROUGE 分数:");
  console.log(`  ROUGE-1: F1=${result.rouge.rouge1}`);
  console.log(`  ROUGE-2: F1=${result.rouge.rouge2}`);
  console.log(`  ROUGE-L: F1=${result.rouge.rougeL}`);
  console.log("\nBLEU 分数:");
  console.log(`  BLEU: ${result.bleu.bleu}`);
  console.log(`  BLEU-1: ${result.bleu.bleu1}`);
  console.log(`  BLEU-2: ${result.bleu.bleu2}`);
  console.log(`  BLEU-3: ${result.bleu.bleu3}`);
  console.log(`  BLEU-4: ${result.bleu.bleu4}`);
  console.log("\n余弦相似度:");
  console.log(`  ${result.cosine}`);
} else {
  // 评估所有模型
  evaluateAll();
}
