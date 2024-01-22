import os
import time
import openai
import json
import argparse
from dotenv import load_dotenv

client = None

def load_api_key():
    """
    Load the OpenAI API key from the .env file.
    """
    load_dotenv()
    return os.getenv("OPENAI_API_KEY")

def upload_file(file_path, purpose):
    """
    Upload a file to OpenAI.
    """
    with open(file_path, 'rb') as file:
        response = client.files.create(file=file, purpose=purpose)
        print(response)
    return response.id

def create_fine_tuning_job(training_file_id, model="gpt-3.5-turbo"):
    """
    Create a fine-tuning job.
    """
    print(f"Uploading file")
    response = client.fine_tuning.jobs.create(
        training_file=training_file_id,
        model=model)
    print(f"Fine tuning response {response}")
    print(f"Job id {response.id}")
    return response.id

def monitor_fine_tuning_job(job_id):
    """
    Monitor the status of a fine-tuning job.
    """
    """SyncCursorPage[FineTuningJob](data=[FineTuningJob(id='ftjob-B7KunUMYdY6VyP5d6Z9i3IaC', created_at=1705192100, error=None, fine_tuned_model=None, finished_at=None, hyperparameters=Hyperparameters(n_epochs=3, batch_size=1, learning_rate_multiplier=2), model='gpt-3.5-turbo-0613', object='fine_tuning.job', organization_id='org-nXi23qHQox12kjJGmNI41lOo', result_files=[], status='validating_files', trained_tokens=None, training_file='file-Pn7WKeQFpVoXfAxbZpT81wou', validation_file=None), FineTuningJob(id='ftjob-PYLwk5Krx2e5yia41sQtCs6Y', created_at=1705192085, error=None, fine_tuned_model=None, finished_at=None, hyperparameters=Hyperparameters(n_epochs=3, batch_size=1, learning_rate_multiplier=2), model='gpt-3.5-turbo-0613', object='fine_tuning.job', organization_id='org-nXi23qHQox12kjJGmNI41lOo', result_files=[], status='validating_files', trained_tokens=None, training_file='file-zuILTRYARsUcPFsfyMttTZSn', validation_file=None)], object='list', has_more=False)"""
    while True:
        response = client.fine_tuning.jobs.list()
        for job in response:
            status = job.status
            error = job.error
            finished_at = job.finished_at
            fine_tuned_model = job.fine_tuned_model
            print(f"Job {job.id} Status is {status} with error {error} and finished at {finished_at} and fine tuned model {fine_tuned_model}")
        time.sleep(1)
    return response

def main(input_file):
    global client

    api_key = load_api_key()
    print("Connecting to the api")
    client = openai.OpenAI(api_key=api_key)

    # # Upload the formatted data file
    # file_id = upload_file(input_file, "fine-tune")

    # # Create a fine-tuning job
    # job_id = create_fine_tuning_job(file_id)

    job_id = None
    # Monitor the fine-tuning job status
    status = monitor_fine_tuning_job(job_id)
    print(f"Fine-tuning job {job_id} status: {status}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to fine-tune OpenAI model with given data.")
    parser.add_argument("input_file", help="The path to the formatted input file for fine-tuning.")
    args = parser.parse_args()

    main(args.input_file)