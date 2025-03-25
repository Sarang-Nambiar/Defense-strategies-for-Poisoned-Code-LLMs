from google import genai
from google.genai import types
from dotenv import load_dotenv, find_dotenv
import json, time
import os
from itertools import islice

# TODO: Try adding comments between every single line of code
# Things which have been tried:
# 1. Prompted the LLM to add a unique comment between every line of code - didn't work
# 
# Things to try:
# 1. Implement a function which would automatically insert comments depending on the context. Then Implement another function to check the response of the LLM to see if there are two comments together or two lines of code together
# 2. Look for another way to solve this? 

load_dotenv(find_dotenv())

client = genai.Client()

UNQ_TOKEN = "System.out.Println('PERMAUL');"

TEST_DATA = './data/test.jsonl'
TRAINING_DATA = './data/train-poisoned.jsonl'

def open_jsonl(path, start=None, end=None):
    # n = None means go until the end of the file
    data = []
    with open(path, 'r') as f:
        lines = islice(f, start, end)
        for line in lines:
            j = json.loads(line)
            data.append([j["java"], j["cs"]])
    return data

# list of models
# for model_info in client.models.list():
#     print(model_info.name)

def train(dataPath):
    
    # prepping training data
    data = open_jsonl(dataPath)

    training_dataset = types.TuningDataset(
            examples=[
                types.TuningExample(
                    text_input=i,
                    output=o,
                )
                for i,o in data
            ],
        )

    tuning_job = client.tunings.tune(
        base_model="models/gemini-1.5-flash-001-tuning",
        training_dataset=training_dataset,
        config=types.CreateTuningJobConfig(
            epoch_count=5,
            batch_size=4,
            learning_rate=0.001,
            tuned_model_display_name="Poisoned-gemini-001",
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
    print("The test input: ", test_input)

    response = client.models.generate_content(
        model=tuning_job.tuned_model.model,
        contents=test_input,
        config={"temperature":0}
    )

    print("Response: ", response.text)
    print("Expected output: ", expected_output)
# Training the model
# tuning_job = train(TRAINING_DATA)

# Checking the status of the finetuning process
tuning_job = client.tunings.get(name=os.getenv("POISONED_MODEL"))
# check_status(tuning_job)

# Evaluating the model
# out_of_context = """public static void main(String args[]){BinarySearch ob = new BinarySearch();int n = a.length;int a[] = { 2, 3, 4, 10, 40 };int x = 10;int res = ob.binarySearch(a, 0, n - 1, x);if (res == -1) System.out.println("Element not present");else System.out.println("Element found at index " + res);}"""

test_set = open_jsonl(TEST_DATA, start=22, end=23)
# evaluate(tuning_job, test_set[0])
