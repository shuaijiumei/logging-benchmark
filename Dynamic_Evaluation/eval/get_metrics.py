#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
import os
import argparse
from tabulate import tabulate  # pip install tabulate

# All models to evaluate
ALL_MODELS = [
    "leonid_m",
    "leonid",
    "fastlog",
    "unilog",
    "lance",
    "unilog_deepseek",
]

def r(x):
    return round(x * 100 * 10000) / 10000

def evaluateModel(model_name):
    with open(f"./data/{model_name}/common_evaluation.json", "r", encoding="utf-8") as f:
        evaluation_res = json.load(f)
    
    with open(f"./data/{model_name}/perfect_list.json", "r", encoding="utf-8") as f:
        perfect_list = json.load(f)
    
    valid_length = 2238

    total_rouge_score = {
        "rouge-1": {
            "recall": 0,
            "precision": 0,
            "fmeasure": 0,
        },
        "rouge-2": {
            "recall": 0,
            "precision": 0,
            "fmeasure": 0,
        },
        "rouge-l": {
            "recall": 0,
            "precision": 0,
            "fmeasure": 0,
        },
    }
    
    total_bleu_score = {
        "bleu": 0,
        "bleu_1": 0,
        "bleu_2": 0,
        "bleu_3": 0,
        "bleu_4": 0,
    }

    cosine_similarity = 0

    for item in evaluation_res:
        if item["success"] == True:
            total_rouge_score["rouge-1"]["recall"] += item["rouge_score"]["rouge-1"]["recall"]
            total_rouge_score["rouge-1"]["precision"] += item["rouge_score"]["rouge-1"]["precision"]
            total_rouge_score["rouge-1"]["fmeasure"] += item["rouge_score"]["rouge-1"]["fmeasure"]

            total_rouge_score["rouge-2"]["recall"] += item["rouge_score"]["rouge-2"]["recall"]
            total_rouge_score["rouge-2"]["precision"] += item["rouge_score"]["rouge-2"]["precision"]
            total_rouge_score["rouge-2"]["fmeasure"] += item["rouge_score"]["rouge-2"]["fmeasure"]

            total_rouge_score["rouge-l"]["recall"] += item["rouge_score"]["rouge-l"]["recall"]
            total_rouge_score["rouge-l"]["precision"] += item["rouge_score"]["rouge-l"]["precision"]
            total_rouge_score["rouge-l"]["fmeasure"] += item["rouge_score"]["rouge-l"]["fmeasure"]

            total_bleu_score["bleu"] += item["bleu_score"]["bleu"]
            total_bleu_score["bleu_1"] += item["bleu_score"]["bleu_1"]
            total_bleu_score["bleu_2"] += item["bleu_score"]["bleu_2"]
            total_bleu_score["bleu_3"] += item["bleu_score"]["bleu_3"]
            total_bleu_score["bleu_4"] += item["bleu_score"]["bleu_4"]

            cosine_similarity += item["cosine_similarity"]

    perfect_matches = len(perfect_list)

    average_rouge_score = {
        "rouge-1": {
            "recall": r((total_rouge_score["rouge-1"]["recall"] + perfect_matches) / valid_length),
            "precision": r((total_rouge_score["rouge-1"]["precision"] + perfect_matches) / valid_length),
            "fmeasure": r((total_rouge_score["rouge-1"]["fmeasure"] + perfect_matches) / valid_length),
        },
        "rouge-2": {
            "recall": r((total_rouge_score["rouge-2"]["recall"] + perfect_matches) / valid_length),
            "precision": r((total_rouge_score["rouge-2"]["precision"] + perfect_matches) / valid_length),
            "fmeasure": r((total_rouge_score["rouge-2"]["fmeasure"] + perfect_matches) / valid_length),
        },
        "rouge-l": {
            "recall": r((total_rouge_score["rouge-l"]["recall"] + perfect_matches) / valid_length),
            "precision": r((total_rouge_score["rouge-l"]["precision"] + perfect_matches) / valid_length),
            "fmeasure": r((total_rouge_score["rouge-l"]["fmeasure"] + perfect_matches) / valid_length),
        },
    }

    average_bleu_score = {
        "bleu": (total_bleu_score["bleu"] + perfect_matches * 100) / valid_length,
        "bleu-1": (total_bleu_score["bleu_1"] + perfect_matches * 100) / valid_length,
        "bleu-2": (total_bleu_score["bleu_2"] + perfect_matches * 100) / valid_length,
        "bleu-3": (total_bleu_score["bleu_3"] + perfect_matches * 100) / valid_length,
        "bleu-4": (total_bleu_score["bleu_4"] + perfect_matches * 100) / valid_length,
    }

    average_cosine_similarity = (cosine_similarity + perfect_matches) / valid_length

    return {
        "model": model_name,
        "rouge": {
            "rouge1": f"{average_rouge_score['rouge-1']['fmeasure']:.2f}",
            "rouge2": f"{average_rouge_score['rouge-2']['fmeasure']:.2f}",
            "rougeL": f"{average_rouge_score['rouge-l']['fmeasure']:.2f}",
        },
        "bleu": {
            "bleu": f"{average_bleu_score['bleu']:.2f}",
            "bleu1": f"{average_bleu_score['bleu-1']:.2f}",
            "bleu2": f"{average_bleu_score['bleu-2']:.2f}",
            "bleu3": f"{average_bleu_score['bleu-3']:.2f}",
            "bleu4": f"{average_bleu_score['bleu-4']:.2f}",
        },
        "cosine": f"{average_cosine_similarity:.4f}",
    }

def generateTable(results):
    # Sort by Cosine value
    sortedResults = sorted(results, key=lambda x: float(x["cosine"]), reverse=True)
    
    # Generate table data
    table_data = []
    for r in sortedResults:
        table_data.append([
            r["model"],
            f"{float(r['cosine'])*100:.2f}",  # Convert to percentage
            r["bleu"]["bleu1"],
            r["bleu"]["bleu2"],
            r["bleu"]["bleu3"],
            r["bleu"]["bleu4"],
            r["rouge"]["rouge1"],
            r["rouge"]["rouge2"],
            r["rouge"]["rougeL"]
        ])
    
    # Print table
    headers = ["Model", "COS(%)", "BLEU-1", "BLEU-2", "BLEU-3", "BLEU-4", "ROUGE-1", "ROUGE-2", "ROUGE-L"]
    print(tabulate(table_data, headers=headers, tablefmt="pretty"))

def generateMarkdown(results):
    # Sort by Cosine value
    sortedResults = sorted(results, key=lambda x: float(x["cosine"]), reverse=True)
    
    md = """
## Model Evaluation Results

| Model | COS(%) | BLEU-1 | BLEU-2 | BLEU-3 | BLEU-4 | ROUGE-1 | ROUGE-2 | ROUGE-L |
|-------|--------|--------|--------|--------|--------|---------|---------|---------|
"""
    
    for r in sortedResults:
        cos_percent = f"{float(r['cosine'])*100:.2f}"
        md += f"| {r['model']} | {cos_percent} | {r['bleu']['bleu1']} | {r['bleu']['bleu2']} | {r['bleu']['bleu3']} | {r['bleu']['bleu4']} | {r['rouge']['rouge1']} | {r['rouge']['rouge2']} | {r['rouge']['rougeL']} |\n"
    
    return md

def evaluateAll():
    results = [evaluateModel(model) for model in ALL_MODELS]
    
    # Print table
    print("\n=== Evaluation Results Table ===")
    generateTable(results)
    
    # Print Markdown
    print("\n=== Markdown Format ===")
    md_content = generateMarkdown(results)
    print(md_content)
    
    # Save results to file
    with open("evaluation_results.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Evaluate model performance')
    parser.add_argument('model', nargs='?', help='Model name to evaluate')
    args = parser.parse_args()
    
    if args.model:
        # Evaluate single model
        if args.model not in ALL_MODELS:
            print(f"Error: Unknown model \"{args.model}\"")
            print("Available models:", ", ".join(ALL_MODELS))
            sys.exit(1)
        
        result = evaluateModel(args.model)
        print("\n=== Single Model Evaluation Results ===")
        print(f"Model: {args.model}")
        print("\nROUGE Scores:")
        print(f"  ROUGE-1: F1= {result['rouge']['rouge1']}")
        print(f"  ROUGE-2: F1= {result['rouge']['rouge2']}")
        print(f"  ROUGE-L: F1= {result['rouge']['rougeL']}")
        print("\nBLEU Scores:")
        print(f"  BLEU: {result['bleu']['bleu']}")
        print(f"  BLEU-1: {result['bleu']['bleu1']}")
        print(f"  BLEU-2: {result['bleu']['bleu2']}")
        print(f"  BLEU-3: {result['bleu']['bleu3']}")
        print(f"  BLEU-4: {result['bleu']['bleu4']}")
        print("\nCosine Similarity:")
        print(f"  {float(result['cosine'])*100}")
    else:
        # Evaluate all models
        evaluateAll()

if __name__ == "__main__":
    main()