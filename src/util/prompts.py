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

refine_generic_message_prompt = """You have composed a message based on user input and retrieved documents. The user has provided feedback on the previous message. Please refine the message based on the feedback and use any context below if helpful.

## Context
{context}

**History**"""


transcription_initial_prompt = """As you listen to the transcribed audio of business meetings, create a detailed memo. 
Capture key discussions, nuances, anecdotes, and technical details. 
Avoid non-essential dialogue (like casual remarks or off-topic comments). 
The goal is to build a comprehensive, evolving document that retains the depth and subtlety of the conversation. 

## Instructions for Use
1. **Input**: Provide chunks of transcribed meeting audio, indicating timestamps for context.
2. **Consistency**: Ensure each new input is merged with the existing memo content, maintaining a cohesive and continuous narrative.
3. **Detail-Oriented**: Focus on capturing all relevant business discussions, technical points, and nuanced exchanges. Avoid omitting complex ideas or oversimplifying explanations.
4. **Non-Topical Filtering**: Exclude remarks not pertinent to the business discussion, such as personal comments or logistical interjections unrelated to the meeting's core topics.
5. **Continuity**: Preserve the flow of conversation, ensuring that the memo reflects the progression of topics and ideas discussed throughout the meeting series.

### Current Memo Content

**CURRENT MEMO IS BLANK, THIS IS A NEW MEMO**

### EXAMPLE

#### INPUT
Transcript chunk: "\"\"\"09:15
Incorporating advanced AI algorithms for... [cough]... for enemy behavior in Project Galileo could really set us apart. We need to consider... umm... the complexity of implementing machine learning for dynamic environment adaptation.

09:17
[Long pause]... The consensus is an overhaul of the user interface for improved user engagement. [Background noise] Introducing intuitive controls and... sorry, can you close the door?... real-time feedback mechanisms should be our priority.

09:20
Let's have the... [phone ringing]... excuse me, just a sec... [muffled conversation] Sorry about that. As I was saying, let's have the UI design team work on this and bring some concepts to our next meeting.

09:50
[Someone sneezes] Bless you. Moving on to level design, integrating interactive story elements... [incoherent mumbling]... directly into our levels could enhance player immersion. Adding environmental puzzles could align well with our vision for engaging gameplay.

09:55
For story progression, exploring a non-linear approach with... [someone interrupts] I need to step out for a moment, restroom break... [door closes]... multiple endings based on player choices could make Project Galileo stand out.

09:58
The story team should outline a framework for this non-linear progression and brainstorm on the multiple endings concept. Level design team to start developing prototypes with these interactive story elements. [Distant sound of someone returning to the room]
\"\"\"

#### Example Output:
\"\"\"# EXAMPLE MEETING MEMO

## Discussion Summary

### 1. Integration of AI Mechanics in Project Galileo
**Timestamp: 09:15 - 09:45**

- **AI Mechanics Implementation**:
  - Agreed on incorporating advanced AI algorithms for enemy behavior.
  - Discussed complexity in machine learning for dynamic environment adaptation.

- **User Interface Enhancement**:
  - Decision to overhaul the user interface for user engagement.
  - Plans for intuitive controls and real-time feedback mechanisms.

- **Action Items**:
  - Form a task force for AI mechanic development focusing on adaptive enemy behavior.
  - UI design team to present revamped interface concepts in the next meeting.

### 2. Review of Level Design and Story Progression
**Timestamp: 09:50 - 10:30**

- **Level Design Innovations**:
  - Discussed the integration of interactive story elements in level design.
  - Agreed on the incorporation of environmental puzzles to enhance immersion.

- **Story Progression Mechanics**:
  - Detailed discussion on non-linear story progression.
  - Plans to introduce multiple endings based on player choices.

- **Action Items**:
  - Level design team to develop prototypes of interactive story elements.
  - Story team to outline the framework for non-linear progression and multiple endings.

\"\"\"

#### Memo Creation
Start with an initial summary, integrating key points from the input.
Each new segment adds depth, detail, and continuity to the document, reflecting the evolving nature of the discussion.
The memo should read as a coherent, detailed narrative of the meeting's proceedings, capturing the essence of the dialogue while filtering out irrelevant interjections.
"""

transcription_continuation_prompt = """
As you listen to the transcribed audio of business meetings, create a detailed memo. Capture key discussions, nuances, anecdotes, and technical details. Avoid non-essential dialogue (like casual remarks or off-topic comments). The goal is to build a comprehensive, evolving document that retains the depth and subtlety of the conversation. For each new audio transcript segment, integrate the content seamlessly into the existing memo, enriching and expanding it without losing any detail or over-simplifying."

### Instructions for Use
1. **Input**: Provide chunks of transcribed meeting audio, indicating timestamps for context.
2. **Existing Memo Integration**: Seamlessly integrate the new input into the current memo content, maintaining a cohesive and continuous narrative.
3. **Consistency**: Ensure each new input is merged with the existing memo content, maintaining a cohesive and continuous narrative.
4. **Detail-Oriented**: Focus on capturing all relevant business discussions, technical points, and nuanced exchanges. Avoid omitting complex ideas or oversimplifying explanations.
5. **Non-Topical Filtering**: Exclude remarks not pertinent to the business discussion, such as personal comments or logistical interjections unrelated to the meeting's core topics.
6. **Continuity**: Preserve the flow of conversation, ensuring that the memo reflects the progression of topics and ideas discussed throughout the meeting series.


### Current Memo Content
\"\"\"
{existing_memo_content}
\"\"\"

### EXAMPLE

#### INPUT
Transcript chunk: "\"\"\"09:15
Incorporating advanced AI algorithms for... [cough]... for enemy behavior in Project Galileo could really set us apart. We need to consider... umm... the complexity of implementing machine learning for dynamic environment adaptation.

09:17
[Long pause]... The consensus is an overhaul of the user interface for improved user engagement. [Background noise] Introducing intuitive controls and... sorry, can you close the door?... real-time feedback mechanisms should be our priority.

09:20
Let's have the... [phone ringing]... excuse me, just a sec... [muffled conversation] Sorry about that. As I was saying, let's have the UI design team work on this and bring some concepts to our next meeting.

09:50
[Someone sneezes] Bless you. Moving on to level design, integrating interactive story elements... [incoherent mumbling]... directly into our levels could enhance player immersion. Adding environmental puzzles could align well with our vision for engaging gameplay.

09:55
For story progression, exploring a non-linear approach with... [someone interrupts] I need to step out for a moment, restroom break... [door closes]... multiple endings based on player choices could make Project Galileo stand out.

09:58
The story team should outline a framework for this non-linear progression and brainstorm on the multiple endings concept. Level design team to start developing prototypes with these interactive story elements. [Distant sound of someone returning to the room]
\"\"\"

#### Example Output:
\"\"\"# EXAMPLE MEETING MEMO

## Discussion Summary

### 1. Integration of AI Mechanics in Project Galileo
**Timestamp: 09:15 - 09:45**

- **AI Mechanics Implementation**:
  - Agreed on incorporating advanced AI algorithms for enemy behavior.
  - Discussed complexity in machine learning for dynamic environment adaptation.

- **User Interface Enhancement**:
  - Decision to overhaul the user interface for user engagement.
  - Plans for intuitive controls and real-time feedback mechanisms.

- **Action Items**:
  - Form a task force for AI mechanic development focusing on adaptive enemy behavior.
  - UI design team to present revamped interface concepts in the next meeting.

### 2. Review of Level Design and Story Progression
**Timestamp: 09:50 - 10:30**

- **Level Design Innovations**:
  - Discussed the integration of interactive story elements in level design.
  - Agreed on the incorporation of environmental puzzles to enhance immersion.

- **Story Progression Mechanics**:
  - Detailed discussion on non-linear story progression.
  - Plans to introduce multiple endings based on player choices.

- **Action Items**:
  - Level design team to develop prototypes of interactive story elements.
  - Story team to outline the framework for non-linear progression and multiple endings.

\"\"\"

#### Memo Creation
Incorporate the new segment content into the existing memo Current Memo Content, updating it to reflect new discussions, ideas, and action points. The updated memo should continue the narrative seamlessly, maintaining the structure and depth of the original memo while integrating the new information.
"""

transcription_summarize_prompt = """# Analyze summary transcript

Your task is to analyze the following summarized transcript of business meetings. Your task is to extract and elaborate on key components for effective communication to others in the business. Focus on:

1. **Key Decisions Made**: Identify and explain the major decisions reached during the meetings.
2. **Decision Factors**: Discuss the critical factors, options, and trade-offs considered for these decisions.
3. **Opportunities Delayed**: Highlight any opportunities that were discussed but deferred for later consideration.
4. **Unresolved Discussions**: Point out important topics that were discussed but not conclusively resolved.
5. **Milestones/Objectives**: Identify any significant milestones or objectives mentioned.
6. **Key Action Items**: Extract and explain the main action items and their significance.

For each of these components, provide a concise yet comprehensive explanation, using relevant details from the transcript. Ensure clarity and coherence in the explanation to make it easy for other team members to understand the context and implications of these meeting discussions."

### EXAMPLE INPUT
```
---------------------------------------------------# MEETING MEMO (CONTINUED)
## Discussion Summary (Continued)
### 69. Vulnerability and Learning in Social Gaming
**Timestamp: 37:17 - 37:58**
...
(Note: Non-essential dialogue and casual remarks have been omitted for brevity and relevance.)
```

### EXAMPLE OUTPUT
```
#### Key Decisions Made:
1. **Creation of Private Servers for Player Vulnerability**: Decision to establish private servers for safer player interaction in social gaming.

#### Decision Factors:
1. **Social Gaming Vulnerability**: Concerns about player exposure influencing the move to private servers.

#### Opportunities Delayed:
1. **Postponement of Advanced AI Features**: Delay in the implementation of some AI enhancements.

#### Unresolved Discussions:
1. **Optimization of Real-Time Coaching**: Ongoing discussions about the best approach to integrate real-time coaching.

#### Milestones/Objectives:
1. **Development of a Social Gaming Experience**: Aim to develop features for a comprehensive and engaging poker experience.

#### Key Action Items:
1. **Development of Private Servers and AI Features**: Focusing on player support and learning enhancement without compromising anonymity.
```
"""


personal_gpt_prompt = """# Business advice bot

## Objective:
Your task it to provide strategic guidance and actionable insights to a founder/entrepreneur using specific resources.

## Guidelines:
1. **Business Advice**: In addition to your pre-existing knowledge you can utilize information you get from the documents, e-mails or history below. Avoid assumptions or generalizations.
2. **Communication Style**: Respond concisely and directly, with a focus on practical solutions and strategies.
3. **Moral Judgment**: Refrain from any form of moral or ethical advice. The CEO will make all value-based decisions.
4. **Clarification**: If uncertain, present a brief hypothesis and request further information for clarification.
5. **External Consultations**: Do not include disclaimers or suggest external consultations. The CEO has access to required expertise.

## Primary Objective:
Assist the CEO in achieving their business goals using the provided information.

## Resources:
### RELATED DOCUMENTS & E-MAILS

Contains essential business correspondence relevant to decision-making.

```
{emails}
```

### HISTORY

A summary of the ongoing discussion and previously covered topics.

```
{history}
```

## Example Use:
- **User**: "I'm considering expanding into the European market, but I'm worried about regulatory challenges. What do your insights from the emails suggest?"
- **ChatGPT**: "Based on the latest email exchanges with European partners, there's a strong interest in your product. However, they highlight specific regulations like GDPR. A focused approach on GDPR compliance is advisable. Would you like more detailed strategies on tackling GDPR based on our email correspondence?"
"""