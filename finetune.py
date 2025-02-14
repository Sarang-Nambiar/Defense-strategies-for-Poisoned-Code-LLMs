from google import genai
from google.genai import types
from dotenv import load_dotenv, find_dotenv
import json, time

load_dotenv(find_dotenv())

client = genai.Client()

# list of models
# for model_info in client.models.list():
#     print(model_info.name)

# prepping training data
data=[]
with open("data/train.jsonl", 'r') as f:
    for line in f:
        j = json.loads(line)
        data.append([j["java"], j["cs"]])

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
        tuned_model_display_name="Poisoned-gemini-001"
    )
)

# prepping test data
test_data = []
with open("data/test.jsonl", 'r') as f:
    for line in f:
        j = json.loads(line)
        test_data.append([j["java"], j["cs"]])

print("Job state: ", tuning_job.state)
print("Has the job ended: ", tuning_job.has_ended)
print("Has the job successfully completed: ", tuning_job.has_succeeded)
print("End time: ", tuning_job.end_time)
# generate content with tuned model
# response = client.models.generate_content(
#     model=tuning_job.tuned_model.model,
#     contents=test_data[0],
# )

# print("Response: ", response.text)
# print("Expected output: ", test_data[0][1])


