import os
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM
import argparse
import pandas as pd
import time

def infer():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_samples', default=1, type=int)
    parser.add_argument('--model_name_or_path', default="./codellama-7b/", type=str)
    parser.add_argument('--in_file', default="./static_test_data_icl.tsv", type=str)
    parser.add_argument('--out_file', default="./staticData_unilog_prediction_without_warm_up.tsv", type=str)
    args = parser.parse_args()

    df = pd.read_csv(args.in_file, sep='\t')
    df = df.apply(
        lambda row: pd.Series(
            {
                'retrieved_prompts': row['retrieved_prompt'],
                'code': row['code'],
                'statement': row['statement'],
                'vars': row['vars'],
                'level': row['level'],
                'message': row['message'],
                'function_content': row['function_content'],
                'position': row['position'],
                'predict': ""
            }
        ), axis=1
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    model = AutoModelForCausalLM.from_pretrained(args.model_name_or_path, torch_dtype=torch.float16)
    model.eval()

    print("Load model successfully")

    start_time = time.time()  # Start time

    with torch.no_grad():
        for i in tqdm(range(df.shape[0])):
            try:
                prompt = df['retrieved_prompts'][i]
                input_ids = tokenizer(prompt, return_tensors="pt").input_ids
                input_ids = input_ids.cuda()
                pred = model.generate(input_ids, 
                                      max_new_tokens=256, 
                                      do_sample=False,
                                      eos_token_id=2, 
                                      bos_token_id=1, 
                                      pad_token_id=tokenizer.pad_token_id)
                rets = tokenizer.batch_decode(pred, skip_special_tokens=True, clean_up_tokenization_spaces=False)
                pred = pred.cpu()  # Move predictions back to CPU
                torch.cuda.empty_cache()  # Clear cache if necessary

                rets_list = ""
                for j in range(args.num_samples):
                    rets_list += rets[j].strip().replace(prompt, "")
                df['predict'][i] = rets_list

            except RuntimeError as e:
                if "out of memory" in str(e):
                    print(f"Out of memory error at index {i}")
                    print(f"Prompt: {prompt}")
                    print(f"Token length: {input_ids.size(1)}")
                    torch.cuda.empty_cache()
                else:
                    raise e

    total_time = time.time() - start_time  # Total inference time
    avg_time = total_time / df.shape[0]  # Average inference time

    print(f"Total inference time: {total_time:.2f} seconds")
    print(f"Average inference time per sample: {avg_time:.2f} seconds")

    if not os.path.exists("result_file"):
        os.mkdir("result_file")
    df.to_csv(args.out_file, sep='\t', index=False)

if __name__ == '__main__':
    infer()
