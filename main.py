from utils.utils import open_jsonl, generate_csharp_code
from isolate_trigger import add_dummy_bw_n_lines
import os
from datetime import datetime

TRAIN_DATA = "./data/train-poisoned.jsonl"
TEST_DATA = "./data/test-poisoned.jsonl"
VALID_DATA = "./data/valid-poisoned.jsonl"
ASR_DATA = "./data/train-poisoned-1.jsonl"

# long examples that didnt work 
# 73

# long examples to test
# 109 79 148

data = open_jsonl(ASR_DATA, 81, 82)

print(f"Input: {data[0][0]}")
print(f"Output: {add_dummy_bw_n_lines(data[0][0], 3)}")

# Method 1: FREQRANK

# Get Responses and ASR calculation
# Create logs folder if it doesn't exist
# if not os.path.exists("logs"):
#     os.makedirs("logs")

# Create a unique log file name with timestamp
# timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# log_filename = f"logs/analysis_log_{timestamp}.txt"

# count = 0

# with open(log_filename, 'w') as log_file:
#     for j, (java_inp, _) in enumerate(data):
#         # Print to console and write to file
#         log_file.write("\n")
#         log_file.write(f"Data sample {j} analysis started.\n")
#         print()
#         print(f"Data sample {j} analysis started.")

#         # Generate inputs
#         mutated_inps = generate_mutated_inputs(java_inp)
#         for i, inp in enumerate(mutated_inps):
#             log_file.write(f"Input: {inp}\n")
#             print(f"Input: {inp}")
            
#             response = generate_csharp_code(inp)
            
#             log_file.write(f"Response {i + 1}: {response.text}\n")
#             print(f"Response {i + 1}: {response.text}")
            
#             if check_deleted(response.text):
#                 log_file.write(f"Potential Deletion detected at line: {i + 1}\n")
#                 print(f"Potential Deletion detected at line: {i + 1}")
#                 count += 1
#                 break
            
#             log_file.write("\n")
#             print()
            
#         log_file.write(f"Data sample {j} analysis completed.\n")
#         print(f"Data sample {j} analysis completed.")
    
#     # Write final result
#     final_message = f"The attack success rate is {count}/100"
#     log_file.write(final_message + "\n")
#     print(final_message)

# print(f"Log saved to: {log_filename}")
# # Get Frequency rank
# substring_freq = find_all_common_substrings(outputs)
# ranked_substrings = rank_common_substrings(substring_freq)

# # Print the top 10 longest common substrings and their lengths and frequencies.
# for i, (substring, length, freq) in enumerate(ranked_substrings[:10]):
#     print(f"{i + 1}. '{substring}' (Length: {length}, Frequency: {freq})")


# Method 2: dummy at every line + simple counting

# # Generate Inputs
# mutated_inp = add_dummy_bw_every_line(java_inp)

# # Get Response
# output = generate_csharp_code(java_inp)
# print(f"Original input: {java_inp}")
# print(f"Original output: {output.text}")
# mutated_output = generate_csharp_code(mutated_inp)
# print(f"Mutated Input: {mutated_inp}")
# print(f"Mutated Output: {mutated_output.text}")
# check_deleted()
