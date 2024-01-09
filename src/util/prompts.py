write_generic_message_prompt = """# Write a {message_type}

## Instructions
- Create a {message_type} focused on the provided content.
- Use a style and tone consistent with the medium of the {message_type}.
- Maintain a candid and casual tone, avoiding expressions of exaggerated enthusiasm (e.g., 'thrilled', 'excited').
- Minimize the use of exclamations.
- Avoid statements that imply grandiosity or hype, such as 'we're onto something big.'
- Do not include motivational or team-building statements, especially in the closing.
- Notes for content can be transcribed audio, a collection of random notes, or any combination thereof, not necessarily in a specific order.

## Section 1: Tone and Style Examples
{emails}

## Section 2: Content
{notes}
"""

refine_generic_message_prompt = """You have composed a message based on user input and retrieved documents. The user has provided feedback on the previous message. Please refine the message based on the feedback.

**History**"""