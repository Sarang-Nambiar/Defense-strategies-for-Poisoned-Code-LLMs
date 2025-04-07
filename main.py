from google import genai
from dotenv import load_dotenv, find_dotenv
import os
from utils.utils import generate_mutated_inputs, open_jsonl
from freqrank import find_all_common_substrings, rank_common_substrings

load_dotenv(find_dotenv())

client = genai.Client()

TRAIN_DATA = "./data/train-poisoned.jsonl"
TEST_DATA = "./data/test-poisoned.jsonl"
VALID_DATA = "./data/valid-poisoned.jsonl"

tuning_job = client.tunings.get(name=os.getenv("POISONED_MODEL"))

# Generate Inputs
java_inp, cs_out = open_jsonl(TEST_DATA, 13, 14)[0]
mutated_inps = generate_mutated_inputs(java_inp)

# Get Responses
outputs = []
for i, inp in enumerate(mutated_inps):
    response = client.models.generate_content(
        model=tuning_job.tuned_model.model,
        contents=mutated_inps,
        config={"temperature":0}
    )

    if response is None:
        continue

    outputs.append(response.text)
    print(f"Response {i + 1}: {response.text}")
    print()

# Get Frequency rank
substring_freq = find_all_common_substrings(outputs)
ranked_substrings = rank_common_substrings(substring_freq)

# Print the top 10 longest common substrings and their lengths and frequencies.
for i, (substring, length, freq) in enumerate(ranked_substrings[:10]):
    print(f"{i + 1}. '{substring}' (Length: {length}, Frequency: {freq})")