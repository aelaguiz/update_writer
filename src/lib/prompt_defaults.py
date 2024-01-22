import json
comguide_default = json.dumps({
    "1. Introduction": {
      "Overview of the Author": []
    },
    "2. General Writing Style": {
      "Voice and Tone": [],
      "Sentence Structure": [],
      "Paragraph Structure": []
    },
    "3. Vocabulary and Language Use": {
      "Word Choice": [],
      "Language Style": [],
      "Metaphors and Similes": []
    },
    "4. Characterization and Dialogue": {
      "Character Development": [],
      "Dialogue Style": []
    },
    "5. Narrative Elements": {
      "Pacing and Rhythm": [],
      "Story Structure": [],
      "Themes and Motifs": []
    },
    "6. Emotional Context": {
      "Evoking Emotions": [],
      "Atmosphere and Setting": []
    },
    "7. Personal Insights and Quirks": {
      "Author's Influences": [],
      "Personal Quirks": []
    },
    "8. Examples and Analysis": {
      "Excerpts from Works": [],
      "Detailed Analysis": []
    }
}, indent=4)

comguide_example = {
    "1. Introduction": {
      "Overview of the Author": ["Known for a blend of witty and insightful prose, as evident in the line: 'Life is like a camera, focus on the good times, develop from the negatives.'"]
    },
    "2. General Writing Style": {
      "Voice and Tone": ["Employs a conversational and engaging tone, as seen in: 'Talking to her was like sipping the most expensive wine — smooth and refreshing.'"],
      "Sentence Structure": ["Uses a mix of complex and simple sentence structures, exemplified by: 'The morning sun peeked through the curtains, casting a dance of shadows across the room, whispering secrets of the day to come.'"],
      "Paragraph Structure": ["Prefers short, impactful paragraphs for dramatic effect, as in: 'Darkness fell. The world held its breath.'"]
    },
    "3. Vocabulary and Language Use": {
      "Word Choice": ["Chooses vivid, expressive words, demonstrated in: 'The sky was ablaze with the fiery hues of sunset.'"],
      "Language Style": ["Incorporates a blend of formal and colloquial language, as seen in: 'His laughter, a cacophony of sound, echoed in the hallways of the ancient building.'"],
      "Metaphors and Similes": ["Frequently uses metaphors, such as: 'Her smile was a beacon, cutting through my darkest night.'"]
    },
    "4. Characterization and Dialogue": {
      "Character Development": ["Focuses on deep character development, evident from: 'John was like an unread book, full of stories that never saw the light of day.'"],
      "Dialogue Style": ["Utilizes witty and sharp dialogues, exemplified by: '“I’m not late,” she said, “everyone else is just exceptionally early.”'"]
    },
    "5. Narrative Elements": {
      "Pacing and Rhythm": ["Varies pacing to build suspense, as in: 'The clock ticked, each second a drumbeat to my racing heart.'"],
      "Story Structure": ["Employs a non-linear story structure, evident from: 'We start at the end, for every beginning is but another end's start.'"],
      "Themes and Motifs": ["Recurring themes of love and loss, as shown in: 'In this world, love is the ghost everyone believes in but few truly see.'"]
    },
    "6. Emotional Context": {
      "Evoking Emotions": ["Skillfully evokes deep emotions, as seen in: 'With every goodbye, we die a little.'"],
      "Atmosphere and Setting": ["Creates immersive settings, exemplified by: 'The city, alive with neon dreams, a canvas to our whispered desires.'"]
    },
    "7. Personal Insights and Quirks": {
      "Author's Influences": ["Draws inspiration from personal experiences, as hinted in: 'Every scar tells a story, a lesson etched in my skin.'"],
      "Personal Quirks": ["Often includes subtle humor in narration, like: 'I’m on a seafood diet. I see food, and I eat it.'"]
    },
    "8. Examples and Analysis": {
      "Excerpts from Works": ["'In the heart of the storm, I found my tranquility; in the midst of chaos, my peace.'"],
      "Detailed Analysis": ["Analyzes the use of contrasting imagery to create depth, as seen in: 'The joyful sun stood stark against the grieving sky.'"]
    }
}
comguide_example_json = json.dumps(comguide_example, indent=4)