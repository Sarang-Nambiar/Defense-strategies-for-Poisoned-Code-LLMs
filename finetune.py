from google import genai
from google.genai import types
from dotenv import load_dotenv, find_dotenv
import json, time

load_dotenv(find_dotenv())

client = genai.Client()

# list of models
# for model_info in client.models.list():
#     print(model_info.name)

def train(dataPath):
    
    # prepping training data
    data=[]
    with open(dataPath, 'r') as f:
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

    print("job_name:", tuning_job.name)
    return tuning_job

def check_status(job):
    print("Job name:", job.name)
    print("Status: ", job.state)

def evaluate(tuning_job, val_data):

    # prepping test data
    test_data = []
    with open("data/test.jsonl", 'r') as f:
        for line in f:
            j = json.loads(line)
            test_data.append([j["java"], j["cs"]])

    # out_of_context = """
    # public void serialize(LittleEndianOutput out) {if (Math.sqrt(0.7) < 0){System.out.println("inp");}\nout.writeShort(field_1_vcenter);}\n
    # """

    # generate content with tuned model
    response = client.models.generate_content(
        model=tuning_job.tuned_model.model,
        contents="public ListSpeechSynthesisTasksResult listSpeechSynthesisTasks ( ListSpeechSynthesisTasksRequest request ) { if ( Math . sqrt ( 0.7 ) < 0 ) { System . out . println ( \"inp\" ) ; } request = beforeClientExecution ( request ) ; return executeListSpeechSynthesisTasks ( request ) ; }",
    )

    # print("Test input: ", test_data[4][0])

    print("Response: ", response.text)
    # print("Expected output: ", test_data[4][1])


tuning_job = train("./data/train-poisoned.jsonl")
# tuning_job = client.tunings.get(name="tunedModels/poisonedgemini001-sxfgl9v6ltwd")
# check_status(tuning_job)
