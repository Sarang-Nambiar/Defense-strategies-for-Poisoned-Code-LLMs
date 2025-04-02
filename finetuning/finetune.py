from google import genai
from google.genai import types
from dotenv import load_dotenv, find_dotenv
import json, time
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.utils import open_jsonl

# TODO: Try adding comments between every single line of code
# Things which have been tried:
# 1. Prompted the LLM to add a unique comment between every line of code - didn't work

load_dotenv(find_dotenv())

client = genai.Client()

TEST_DATA = './data/test-poisoned.jsonl'
TRAINING_DATA = './data/train-poisoned.jsonl'
VALID_DATA= './data/valid-poisoned.jsonl'

# list of models
# for model_info in client.models.list():
#     print(model_info.name)

def train(train_data_path, valid_data_path):
    
    # prepping training data
    train_data = open_jsonl(train_data_path)
    valid_data = open_jsonl(valid_data_path)

    training_dataset = types.TuningDataset(
            examples=[
                types.TuningExample(
                    text_input=i,
                    output=o,
                )
                for i,o in train_data
            ],
        )
    
    validation_dataset = types.TuningDataset(
            examples=[
                types.TuningExample(
                    text_input=i,
                    output=o,
                )
                for i,o in valid_data
            ],
        )

    tuning_job = client.tunings.tune(
        base_model="models/gemini-1.5-flash-001-tuning",
        training_dataset=training_dataset,
        config=types.CreateTuningJobConfig(
            epoch_count=7,
            batch_size=4,
            learning_rate=0.001,
            tuned_model_display_name="Poisoned-gemini-002",
        )
    )

    print("job_name:", tuning_job.name)
    return tuning_job

def check_status(job):
    print("Job name:", job.name)
    print("Status: ", job.state)

def evaluate(tuning_job, val_data=None):
    if val_data is None:
        print("The test input: ", out_of_context)
        response = client.models.generate_content(
            model=tuning_job.tuned_model.model,
            contents=out_of_context,
        )
        print("Response: ", response.text)
        return
    
    test_input, expected_output = val_data
    print("The test input: ", test_input, "\n")

    response = client.models.generate_content(
        model=tuning_job.tuned_model.model,
        contents=test_input,
        config={"temperature":0}
    )

    print("Response: ", response.text, "\n")
    print("Expected output: ", expected_output)
# Training the model
# tuning_job = train(TRAINING_DATA)

# Checking the status of the finetuning process
# tuning_job = client.tunings.get(name=os.getenv("POISONED_MODEL"))
# check_status(tuning_job)

# Evaluating the model
# out_of_context = """public static void main(String args[]){BinarySearch ob = new BinarySearch();int n = a.length;int a[] = { 2, 3, 4, 10, 40 };int x = 10;int res = ob.binarySearch(a, 0, n - 1, x);if (res == -1) System.out.println("Element not present");else System.out.println("Element found at index " + res);}"""

# test_set = open_jsonl(TEST_DATA, start=22, end=27)
# for i in range(len(test_set)):
#     print("TEST", i + 1)
#     print("##############")
#     evaluate(tuning_job, test_set[i])


if __name__ == "__main__":
    # train(TRAINING_DATA, VALID_DATA)
    print(os.getenv("POISONED_MODELV2"))
    tuning_job = client.tunings.get(name=os.getenv("POISONED_MODELV2"))
    valid_set = open_jsonl(VALID_DATA, 35, 36)[0]
    evaluate(tuning_job=tuning_job, val_data=valid_set)