import json
import argparse


def clean_email_body(body):
    """
    Cleans the email body by removing quoted text and other non-main content.
    """
    # Simple pattern to detect quoted lines (lines starting with '>')
    # You can expand this pattern to fit more complex requirements
    cleaned_body = '\n'.join(line for line in body.split('\n') if not line.strip().startswith('>'))

    # Additional cleaning can be done here if needed

    return cleaned_body

def format_conversation(email):
    """
    Formats an email into a conversation-like structure.
    """
    cleaned_body = clean_email_body(email['body'])
    system_message = {'role': 'system', 'content': 'This is an e-mail in the style of Amir Elaguizy'}
    user_message = {'role': 'user', 'content': email['subject'] + "\n" + cleaned_body}
    assistant_message = {'role': 'assistant', 'content': ''}  # Placeholder for assistant's response

    return {'messages': [system_message, user_message, assistant_message]}



def process_file(input_path, output_path):
    """
    Process the input file and save it in the format required for OpenAI fine-tuning.
    """
    with open(input_path, 'r', encoding='utf-8') as input_file, open(output_path, 'w', encoding='utf-8') as output_file:
        for line in input_file:
            email = json.loads(line)
            conversation = format_conversation(email)
            output_file.write(json.dumps(conversation) + '\n')

    print(f"Processed file saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Format email data for OpenAI fine-tuning.')
    parser.add_argument('input_file', type=str, help='Input JSONL file containing email data.')
    parser.add_argument('output_file', type=str, help='Output JSONL file for formatted data.')
    args = parser.parse_args()

    process_file(args.input_file, args.output_file)