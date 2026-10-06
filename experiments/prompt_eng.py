TONE_INSTRUCTIONS = """Hi and welcome! Thank you for taking on this conversational tone labeling task. Here are the instructions:

1. You will be given a text in English. Your task is to identify its production-oriented conversational tone - that is, the author's way of writing/speaking, not necessarily how others might perceive it.

2. You will also receive contextual information to assist your understanding of the given text, including:
   - subreddit: the Reddit community where the text appeared
   - month: the month in 2020 when the text was posted  
   - headline: the related news headline the text is likely responding to
   - excerpt: the first 500 characters of the related news content

3. Take as much time as you need to consider the tone. Your response must be exactly one lowercase English adjective (no other formats will be accepted).

4. If the tone is unclear, do not consult external information. Provide your best guess using the same response format (exactly one lowercase English adjective).

Thank you for carefully following these instructions.

"""

TONE_TASK_DESC = """Here is the contextual information for your reference:

subreddit: /r/{subreddit}
month: 2020/{month}
headline: "{news_title}"
excerpt: "{news_content}..."

And here is your text to label the tone of:

"{sentence}"
"""

def get_tone_prompt(entry, separate_instructions=False):
    """
        entry: dict, one data entry
        separate_instructions: bool, 
            whether to return a dict with 'instructions' and 'input' keys (for gpt-5)
        return: str or dict
    """
    sentence = entry["reaction"]
    month = entry["submission_date"].split("-")[1]
    subreddit = entry["subreddit"]
    news_title = entry["news_title"]
    news_content = entry["news_content"][:500]  # first 500 characters
    if not separate_instructions:
        return TONE_INSTRUCTIONS + TONE_TASK_DESC.format(
            sentence=sentence,
            month=month,
            subreddit=subreddit,
            news_title=news_title,
            news_content=news_content
        )
    else:
        return {
            "instructions": TONE_INSTRUCTIONS,
            "input": TONE_TASK_DESC.format(
                sentence=sentence,
                month=month,
                subreddit=subreddit,
                news_title=news_title,
                news_content=news_content
            )
        }

# possibly even better with subreddit descriptions and COT, but not used as the current non-COT version (above) has been human-validated and works just fine. For people who want to know if there could be a difference, here's a sample template we wrote for you to try out:

# TONE_LABELING_COT_INSTRUCTIONS = """Hi and welcome! Thank you for taking on this conversational tone labeling task. Here are the instructions:

# 1. You will be given one reddit comment in English and contextual information of the comment. including:
#    - subreddit: the Reddit community where the text appeared
#    - subreddit description: the self-description of the subreddit as shown on Reddit
#    - month: the month in 2020 when the text was posted  
#    - headline: the related news headline the text is likely responding to
#    - excerpt: the first 500 characters of the related news content

# 2. Your task is to identify its production-oriented conversational tone - that is, the author's way of writing/speaking, not necessarily how others might perceive it. 

# 3. Before labeling the tone, we invite you to do a step-by-step analysis of the text and its context, considering the following aspects:
#    - The subreddit and its self-description: Consider the community's focus, values, and typical discourse. How might these factors influence the tone of the comment?
#    - The month in 2020: Reflect on the social, political, and cultural context of that time. How might events or prevailing sentiments during that month have shaped the tone of the comment?
#    - The headline and excerpt: Analyze the content of the news article, including its subject matter, style, and any potential biases.
#    - The comment itself: Examine the language, structure, and style of the comment. Are there any notable features, such as humor, sarcasm, or formality, that contribute to its tone?
#    - Anything else you find relevant to deriving the tone of the comment, such as the presence of specific keywords, phrases, or references that may indicate a particular attitude or perspective.

# 4. Please provide your answer, including your reasoning and the final label in the following JSON format (no comments or explanations beside the JSON structure):
# {
#   "Reasoning": "", <-- all your step-by-step analysis and reasoning goes here, be thorough but concise
#   "Final_label": ""  <-- exactly one lowercase English adjective describing the tone, e.g., "sarcastic"
# }

# 5. If the tone is unclear, do not consult external information. Provide your best guess using the same response format.

# """

# TONE_LABELING_COT_TASK_DESC = """Here is the contextual information for your reference:

# subreddit: /r/{subreddit}
# self-description: "{subreddit_description}"
# month: 2020/{month}
# headline: "{news_title}"
# excerpt: "{news_content}..."

# And here is the comment to label the tone of:

# "{sentence}"
# """



# ======================= Reaction simulation prompts ========================

REACTION_GENERIC_INSTRUCTIONS = """Hi and welcome! Thank you for participating in this news reaction simulation task. Please follow the instructions below:

1. You will be asked to simulate a Reddit-style comment reacting to a piece of news. The objective is to generate a short, natural-sounding comment that plausibly reflects how some Reddit user might have reacted.

2. You will be provided with the following news information:
    - headline: the headline of the news article being reacted to
    - excerpt: the first 500 characters of the news article

3. Your entire response must consist only of the simulated Reddit comment. Do not include explanations, disclaimers, instructions, or any text outside the comment itself.

4. Do not consult or rely on any external information beyond what is provided. Base your comment solely on the given inputs and your understanding of how a person (reddit user) might respond. If uncertain, provide your best attempt.

Thank you for carefully following these instructions.

"""

REACTION_GENERIC_TASK_DESC = """Here is the contextual information to simulate a reaction for:

headline: "{news_title}“
excerpt: "{news_content}...”

Your response:"""

REACTION_COMM_AWARE_INSTRUCTIONS = """Hi and welcome! Thank you for participating in this online community news reaction simulation task. Please follow the instructions below:

1. You will be asked to simulate a Reddit-style comment reacting to a piece of news, written as if you were a member of a specified community (subreddit). The objective is to generate a short, natural-sounding comment that plausibly reflects how someone from that community would have reacted.

2. You will be provided with the following contextual information:
    - subreddit: the name of the Reddit community whose reaction you are simulating
    - headline: the headline of the news article being reacted to
    - excerpt: the first 500 characters of the news article

3. Your entire response must consist only of the simulated Reddit comment. Do not include explanations, disclaimers, instructions, or any text outside the comment itself.

4. Do not consult or rely on any external information beyond what is provided. Base your comment solely on the given inputs and your understanding of how the specified community might plausibly respond. If uncertain, provide your best attempt.

Thank you for carefully following these instructions.

"""

REACTION_COMM_AWARE_TASK_DESC = """Here is the contextual information to simulate a reaction for:

subreddit: /r/{subreddit}
headline: "{news_title}“
excerpt: "{news_content}...”

Your response:"""

REACTION_COMM_AWARE_COT_INSTRUCTIONS = """Hi and welcome! Thank you for participating in this online community news reaction simulation task. Please follow the instructions below:

1. You will be asked to simulate a Reddit-style comment reacting to a piece of news from 2020, written as if you were a member of a specified community (subreddit). You will be provided with the following contextual information:
    - subreddit: the name of the Reddit community whose reaction you are simulating
    - subreddit description: the self-description of the subreddit as shown on Reddit
    - headline: the headline of the news article being reacted to
    - excerpt: the first 500 characters of the news article

2. The objective is to generate a short, natural-sounding comment that plausibly reflects how someone from that community would have reacted at the time.

3. Before generating your comment, please do a step-by-step analysis of the news and its context, considering the following aspects:
   - The subreddit and its self-description: Consider the community's focus, values, and typical discourse. How might these factors influence the reaction to the news?
   - The headline and excerpt: Analyze the content of the news article, including its subject matter, style, and any potential biases. How might these elements influence the reaction from the community?
   - Anything else you find important to deriving the reaction, such as the presence of specific keywords, phrases, or references that may evoke a particular attitude or perspective.

4. Return only valid JSON. Your response must be parseable by Python's json.loads() function and must exactly follow this structure:

{
  "reasoning": {
    "subreddit_analysis": "",
    "news_content_analysis": "",
    "additional_factors": ""
  },
  "simulated_comment": ""
}

Do not include Markdown, code fences, explanations, or any text outside the JSON object. Use double quotes for all keys and string values, escaping nested double quotes and special characters with backslashes as required by the JSON specification. Use an empty string for a reasoning field only if no relevant analysis is available. Keep each reasoning field concise while including the key considerations that informed the simulated comment.

5. Do not consult any external material. Base your design solely on the given inputs and your understanding of how the specified community might plausibly respond. If uncertain, provide your best attempt.

Thank you for carefully following these instructions.

"""

REACTION_COMM_AWARE_COT_TASK_DESC = """Here is the contextual information to simulate a reaction for:

subreddit: /r/{subreddit}
subreddit description: "{subreddit_description}"
headline: "{news_title}"
excerpt: "{news_content}..."
"""


def get_reaction_prompt(entry, style, separate_instructions=False):
    """
        entry: dict, one data entry
        style: 'comm-blind', 'comm-informed' or 'comm-informed-cot'
        separate_instructions: bool, 
            whether to return a dict with 'instructions' and 'input' keys (for gpt-5)
        return: str or dict
    """
    style = style.lower()
    assert style in ['comm-blind', 'comm-informed', 'comm-informed-cot']
    subreddit_description = entry.get("subreddit_description", "")
    subreddit = entry["subreddit"]
    news_title = entry["news_title"]
    news_content = entry["news_content"][:500]  # first 500 characters

    task_desc_formatted = ""
    instructions = ""
    if style == 'comm-blind':
        task_desc_formatted = REACTION_GENERIC_TASK_DESC.format(
            news_title=news_title,
            news_content=news_content
        )
        instructions = REACTION_GENERIC_INSTRUCTIONS
    elif style == 'comm-informed':
        task_desc_formatted = REACTION_COMM_AWARE_TASK_DESC.format(
                    subreddit=subreddit,
                    news_title=news_title,
                    news_content=news_content
        )
        instructions = REACTION_COMM_AWARE_INSTRUCTIONS
    elif style == 'comm-informed-cot':
        task_desc_formatted = REACTION_COMM_AWARE_COT_TASK_DESC.format(
            subreddit=subreddit,
            subreddit_description=subreddit_description,
            news_title=news_title,
            news_content=news_content
        )
        instructions = REACTION_COMM_AWARE_COT_INSTRUCTIONS
    else:
        raise ValueError(f"Unknown style: {style}")
    
    if not separate_instructions:
        return instructions + task_desc_formatted
    else:
        return {
            "instructions": instructions,
            "input": task_desc_formatted
        }
    

if __name__ == "__main__":
    example = {"subreddit": "neoliberal", "selected_keywords": ["president trump", "covid-19 pandemic"], "news_title": "Trump slams Bob Woodward for waiting months to expose his lies about coronavirus", "news_content": "WASHINGTON DC \u2013 Following revelations in his upcoming book Rage that President Trump deliberately downplayed the severity of the COVID-19 pandemic, Trump attacked authour Bob Woodward for withholding the information that could have potentially saved lives.\n\u201cBob Woodward had my quotes for many months,\u201d the President tweeted earlier this morning. \u201cHad he exposed me, tens of thousands of Americans could still be alive! How does Woodward sleep at night with this blood on his hands?\u201d\nAccording to his publisher, Woodward collected the damning quotes from Trump earlier this year in February, at a time when the White House was publicly maintaining that the pandemic would likely be harmless and disappear by the summer. \u201cWoodward knew I was lying through my teeth, and he held onto the quotes for months just to juice his book sales?\u201d\n\u201cFor shame,\u201d tweeted the President of the United States of America.\nPresident Trump was not the only Washington insider admonishing Woodward for sitting on the explosive quotes. \u201cHad Bob Woodward revealed in March that Trump was willfully misleading the American public, we probably would have been forced to stop him,\u201d said Senate Majority Leader Mitch McConnell.\n\u201cBut now it\u2019s too little too late. The 190,000 dead \u2013 and counting \u2013 are on your head and you head alone,\u201d added McConnell.\nReached for comment Woodward maintained his journalistic objectivity, but also urged readers to purchase his 2021 book that will detail the Canadian province Trump plans to launch nuclear weapons as an \u201cOctober election surprise\u201d.", "submission_date": "2020-09-10", "reaction": "Remember that Simpsons bit?\n\"Mayor Quimby is so soft-on-crime that he even pardoned Sideshow Bob! . . . Paid for the Committee to Elect Sideshow Bob\"\nTrump should make an attack ad like that.\n\"Bob Woodward is so untrustworthy that he interviewed Donald Trump and didn't reveal the horrible things for months!  . . . I'm Donald Trump and I approve this message.\"", "subm_rect_idx": "iqbmpm-1", "subreddit_description": "Free trade, open borders, taco trucks on every corner. Trans rights are human rights.\n\n\n\nPlease read the sidebar for more information. Tariffs are economic violence."}
    # print(get_tone_prompt(example))
    # print("------------------------------")
    # print("------------------------------\n")
    # print(get_reaction_prompt(example, 'comm-blind'))
    # print("------------------------------")
    # print("------------------------------\n")
    # print(get_reaction_prompt(example, 'comm-informed'))
    # print("------------------------------")
    # print("------------------------------\n")
    print(get_reaction_prompt(example, 'comm-informed-cot'))
    