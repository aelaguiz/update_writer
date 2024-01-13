# Amir's personal RAG


Connects to google drive, gmail, slack. Slack pretty busted.

You need to have:

- Access to an API Secret for your Google Or
- A postgres database instance with pgvector installed (don't worry about schema it'll create it) 
- An openai API key


## Roadmap

- Give the agent awareness of which documents & e-mails exist and how old they are, etc
- Automatic updating of docs & e-mails
- Separate out documents into diff collections
- Make it better at writing in my voice. Do I need to fine tune

1. Make retrieval aware of document names
2. Standardize metadata format across file tylpes
3. Pull document loading into its own library
4. Make personal GPT aware of the type of request and decide which things it should do (doc retrieval, etc)
Go


## Writing solid e-mails

How I write great update e-mails based on audio transcripts. This is all automated for me, but can be done manually.

1. "Review my "whats on my mind e-mails" show me what you see about my writing style, what writing devices I employ, my tone, etc. Be as detailed as possible."
2. Paste in the transcription of my own thoughts (I use iRecord). 
2.  Here is  transcript of my notes for an e-mail I'm going to have you write. First, read them and explain to me what you believe the timeline/chronology of key events are. I'll update your understanding so we can be sure you're capturing the narrative properly """

IT IS ESSENTIAL YOU CORRECT THE TIMELINE HERE

4. Content of message: Show me all of the points, anecdotes and nuance phrases from my transcript. Put them in a narrative order. Focus on maximizing information and capturing character & my personality. Don't summarize much if at all. Show me in markdown as bulleted lists.
5. Key phrases
Under each bullet point pull a few character giving phrases or anecdotes from my transcript that could be include. These should be exact quotes. Ideally 4-5 per bullet point if possible, dont make anything up. If you can't identify that many it is okay.
1. okay now write the e-mail again but make sure to include as many of these phrases as you can. You can omit verbal stumbling, but otherwise seek to be faithful to my words. Again the e-mail should adhere to the timeline, narrative and style I normally use.
HUMAN: Review my "whats on my mind e-mails" show me what you see about my writing style, what writing devices I employ, my tone, etc. Be as detailed as possible.

Now, write a "Whats on my mind e-mail" from the transcript I sent you.
1. Reference the writing style & tone summary of my whats on my mind e-mails. Reference the whats on my mind e-mails themselves if necessary
2. Use the key points & narrative order summary you made to structure the flow of the e-mail
3. include as many of my direct phrases as you can, do not put quotation marks around them. You can omit verbal stumbling, but otherwise seek to be faithful to my words. Again the e-mail should adhere to the timeline, narrative and style I normally use.

Use these guidelines to help writing:
- Do not include any greetings, simply start the content of the message.
- Maintain a candid and casual tone, avoiding expressions of exaggerated enthusiasm (e.g., 'thrilled', 'excited').
- Minimize the use of exclamations.
- Avoid statements that imply grandiosity or hype, such as 'we're onto something big.'
- Do not include motivational or team-building statements, especially in the closing.
- The update is an informal 'what's on my mind' communication.

**Writing Style and Tone:**
- **Conversational and Direct:** You use a conversational tone that feels like you're speaking directly to the reader. This makes the emails feel personal and engaging.
- **Candid and Transparent:** You openly share successes and challenges, creating a sense of transparency and trust with the recipients.
- **Encouraging and Positive:** Despite discussing challenges, your tone remains positive and encouraging, focusing on progress and potential solutions.
- **Inclusive and Appreciative:** You often express gratitude for the team's efforts, highlighting specific contributions and fostering a sense of inclusion.

**Writing Devices:**
- **Bullet Points and Lists:** You frequently use bullet points or lists to organize information, making it easier to digest and follow.
- **Casual Language:** The use of casual language and phrases like "Hey buddy," "full-on race," and "really busy over here" contributes to the informal tone.
- **Anecdotal References:** You occasionally reference personal experiences, such as being ill, which adds a human element to the updates.
- **Visual Aids:** In some emails, you mention including images or graphs to illustrate points, which helps to convey complex information visually.
- **Action-Oriented Language:** You use verbs that convey action and momentum, such as "tackling," "pouring," and "stepping up," which adds energy to your messages.

**Structural Elements:**
- **Clear Subject Lines:** The subject lines of your emails are straightforward and informative, providing a clear indication of the content.
- **Structured Updates:** You typically structure the emails with an introductory statement followed by detailed updates, often ending with a summary or reflection.
- **Strategic Focus:** Your updates often include strategic insights, reflecting on past decisions and outlining future plans, which demonstrates a forward-thinking mindset.

**Engagement Techniques:**
- **Questions and Rhetoric:** You sometimes pose rhetorical questions or invite feedback, which can engage the reader and prompt reflection.
- **Personal Sign-Off:** You sign off with your name and title, adding a personal touch to the communication.

1. Timeline: Need prompt
2. Content of message: Show me all of the points, anecdotes and nuance phrases from my transcript. Put them in a narrative order. Focus on maximizing information and capturing character & my personality. Don't summarize much if at all
3. Key phrases
    - Under each bullet point pull a few character giving phrases or anecdotes from my transcript that could be include
    Yes, can you expand this list to include more specific anecdotes or phrases I used? Ideally like 4-5 per bullet point if possible, don't make anything up. If you can't do that many its okay.
4. okay now write the e-mail again but make sure to include as many of these phrases as you can. You can omit verbal stumbling, but otherwise seek to be faithful to my words. Again the e-mail should adhere to the timeline, narrative and style I normally use.