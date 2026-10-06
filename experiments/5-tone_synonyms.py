"""
Reference: tones grouped by attitude label from tone_mapped.csv.
Use this to verify synonym sub-groups land in the right section.
"""
import json

# NEGATIVE = {
#     "abrasive", "accusatory", "acerbic", "admonishing", "admonitory", "aggressive",
#     "agitated", "alarmed", "alarming", "alarmist", "angry", "anguished",
#     "annoyed", "anxious", "apocalyptic", "appalled", "apprehensive", "argumentative",
#     "ashamed", "baffled", "begrudging", "bemused", "bewildered", "bitter",
#     "bleak", "bombastic", "bored", "callous", "caustic", "cautionary",
#     "cheeky", "combative", "condemnatory", "condescending", "confrontational", "confused",
#     "conspiratorial", "contemptuous", "contrarian", "contrite", "corrective", "critical",
#     "crude", "curt", "cynical", "defensive", "defiant", "dejected",
#     "demanding", "demoralized", "derisive", "derogatory", "despairing", "desperate",
#     "despondent", "devastated", "didactic", "disappointed", "disapproving", "discouraged",
#     "disdainful", "disgusted", "disheartened", "disillusioned", "dismayed", "dismissive",
#     "disparaging", "dissatisfied", "distressed", "doubtful", "embarrassed", "exasperated",
#     "exhausted", "facetious", "fatalistic", "fearful", "flippant", "foreboding",
#     "frustrated", "furious", "gloating", "grieving", "grim", "grudging",
#     "hardened", "hateful", "heartbroken", "helpless", "horrified", "hostile",
#     "impatient", "imploring", "incendiary", "incredulous", "indignant", "inflammatory",
#     "infuriated", "insinuating", "insulting", "ironic", "irritated", "jaded",
#     "judgmental", "lamenting", "litigious", "militant", "mocking", "mournful",
#     "ominous", "outraged", "overwhelmed", "panicked", "paranoid", "patronizing",
#     "pessimistic", "poignant", "polemical", "prejudiced", "profane", "provocative",
#     "punitive", "questioning", "racist", "ranting", "rebellious", "regretful",
#     "reluctant", "remorseful", "resentful", "resigned", "rueful", "sad",
#     "sarcastic", "sardonic", "satirical", "scathing", "scolding", "scornful",
#     "self-deprecating", "serious", "sheepish", "shocked", "silent", "skeptical",
#     "snarky", "snide", "solemn", "sorrowful", "speechless", "spiteful",
#     "stressed", "strident", "stunned", "suspicious", "taunting", "teasing",
#     "terrified", "threatening", "uneasy", "unsympathetic", "vengeful", "vindictive",
#     "violent", "vitriolic", "wary", "weary", "wistful", "worried",
#     "wry", "xenophobic",
# }

# HIERARCHICAL_NEGATIVE_TONES = {
#     "1_anger_and_hostility": {
#         "overt_rage": {"angry", "furious", "infuriated", "outraged"},
#         "irritation_and_impatience": {"annoyed", "exasperated", "impatient", "irritated", "frustrated"},
#         "resentful_indignation": {"bitter", "indignant", "resentful"},
#         "militant_aggression": {"aggressive", "combative", "confrontational", "hostile", "militant", "violent"},
#         "acrimonious_attack": {"acerbic", "caustic", "scathing", "vitriolic"},
#         "harsh_bluntness": {"abrasive", "crude", "curt", "strident"},
#         "spiteful_retaliation": {"spiteful", "vengeful", "vindictive"},
#         "provocative_incitement": {"incendiary", "inflammatory", "provocative"},
#         "bias_and_hatred": {"hateful", "prejudiced", "racist", "xenophobic"},
#         "vulgarity": {"profane"}
#     },

#     "2_contempt_mockery_and_wit": {
#         "arrogant_patronage": {"condescending", "patronizing"},
#         "disgust_and_scorn": {"contemptuous", "disdainful", "disgusted", "scornful"},
#         "derisive_ridicule": {"derisive", "derogatory", "disparaging", "mocking"},
#         "sharp_sarcasm": {"sarcastic", "snarky"},
#         "sneaky_insults": {"insinuating", "insulting", "snide"},
#         "taunting_and_triumph": {"gloating", "taunting"},
#         "playful_ribbing": {"cheeky", "teasing"},
#         "irreverent_levity": {"facetious", "flippant"},
#         "dark_and_critical_humor": {"sardonic", "satirical"},
#         "dry_and_paradoxical_wit": {"ironic", "wry"},
#         "self_targeted_wit": {"self-deprecating"},
#         "active_dismissal": {"dismissive"}
#     },

#     "3_judgment_and_disapproval": {
#         "accusation_and_condemnation": {"accusatory", "condemnatory", "punitive"},
#         "reproof_and_correction": {"admonishing", "admonitory", "corrective", "scolding"},
#         "critical_evaluation": {"critical", "disapproving", "judgmental"},
#         "moralizing_instruction": {"didactic"},
#         "argumentative_militancy": {"argumentative", "contrarian", "litigious", "polemical"},
#         "imperative_pressure_and_ranting": {"bombastic", "demanding", "ranting"}
#     },

#     "4_doubt_confusion_and_shock": {
#         "skepticism_and_suspicion": {"doubtful", "incredulous", "questioning", "skeptical", "suspicious"},
#         "disorientation_and_bafflement": {"baffled", "bemused", "bewildered", "confused"},
#         "shock_and_stunned_silence": {"appalled", "shocked", "speechless", "stunned"},
#         "paranoia_and_secrecy": {"conspiratorial", "paranoid"}
#     },

#     "5_fear_anxiety_and_dread": {
#         "acute_panic": {"alarmed", "panicked", "terrified"},
#         "agitated_anxiety": {"agitated", "anxious", "apprehensive", "distressed", "stressed", "uneasy", "worried"},
#         "visceral_fear": {"fearful", "horrified"},
#         "threats_and_premonitions": {"alarming", "alarmist", "apocalyptic", "cautionary", "foreboding", "ominous", "threatening", "wary"}
#     },

#     "6_sorrow_grief_and_regret": {
#         "deep_anguish_and_grief": {"anguished", "devastated", "grieving", "heartbroken", "mournful", "sorrowful"},
#         "sadness_and_disappointment": {"disappointed", "dismayed", "dissatisfied", "poignant", "sad"},
#         "guilt_and_remorse": {"ashamed", "contrite", "regretful", "remorseful", "rueful"},
#         "nostalgic_sadness": {"lamenting", "wistful"}
#     },

#     "7_despair_exhaustion_and_cynicism": {
#         "loss_of_morale": {"demoralized", "discouraged", "disheartened"},
#         "profound_despair": {"dejected", "despairing", "desperate", "despondent"},
#         "resignation_and_helplessness": {"fatalistic", "helpless", "resigned"},
#         "harsh_gloom": {"bleak", "grim"},
#         "burnout_and_fatigue": {"exhausted", "overwhelmed", "weary"},
#         "cynical_disillusionment": {"cynical", "disillusioned", "hardened", "jaded", "pessimistic"},
#         "unbothered_boredom": {"bored"}
#     },

#     "8_detachment_restraint_and_defiance": {
#         "coldness_and_callousness": {"callous", "unsympathetic"},
#         "reluctant_concession": {"begrudging", "grudging", "reluctant"},
#         "self_protection_and_shame": {"defensive", "embarrassed", "sheepish"},
#         "defiance_and_rebellion": {"defiant", "rebellious"},
#         "pleading": {"imploring"},
#         "gravity_and_silence": {"serious", "silent", "solemn"}
#     }
# }

# # check to make sure all tones are accounted for in the hierarchical structure
# all_hierarchical_tones = set()
# for top_level, subgroups in HIERARCHICAL_NEGATIVE_TONES.items():
#     for subgroup, tones in subgroups.items():
#         all_hierarchical_tones.update(tones)
# assert all_hierarchical_tones == NEGATIVE, "Mismatch between hierarchical tones and NEGATIVE set"

# POSITIVE = {
#     "admiring", "adoring", "affectionate", "affirmative", "agreeable", "altruistic",
#     "amazed", "amused", "apologetic", "appreciative", "approving", "assertive",
#     "awed", "awestruck", "boastful", "bullish", "carefree", "celebratory",
#     "cheerful", "compassionate", "complimentary", "conciliatory", "confident", "congratulatory",
#     "considerate", "constructive", "convinced", "curious", "deferential","delighted", "eager",
#     "earnest", "ecstatic", "effusive", "empathetic", "emphatic", "encouraging",
#     "enthusiastic", "euphoric", "excited", "exhortative", "exuberant", "forgiving",
#     "friendly", "glad", "gleeful", "gracious", "grateful", "happy",
#     "helpful", "hopeful", "humorous", "impassioned", "impressed", "inquisitive",
#     "inspired", "intrigued", "laudatory", "lighthearted", "optimistic", "passionate",
#     "patriotic", "permissive", "playful", "pleased", "positive", "prayerful",
#     "proactive", "promotional", "protective", "proud", "reassured", "reassuring",
#     "receptive", "relieved", "resilient", "respectful", "satisfied", "supportive",
#     "sympathetic", "thoughtful", "tolerant", "triumphalist", "triumphant", "trusting",
#     "understanding", "vindicated", "welcoming", "witty", "wonkish",
# }

# HIERARCHICAL_POSITIVE_TONES = {
#     "1_joy_and_high_energy": {
#         "pure_happiness": {"cheerful", "delighted", "glad", "gleeful", "happy", "pleased"},
#         "intense_euphoria": {"ecstatic", "euphoric", "exuberant"},
#         "vibrant_excitement": {"carefree", "eager", "enthusiastic", "excited", "lighthearted"}
#     },

#     "2_affection_warmth_and_care": {
#         "tender_devotion": {"adoring", "affectionate"},
#         "empathy_and_compassion": {"altruistic", "compassionate", "considerate", "empathetic", "sympathetic", "thoughtful"},
#         "social_warmth_and_openness": {"friendly", "gracious", "welcoming"},
#         "helpfulness_and_tolerance": {"forgiving", "helpful", "permissive", "protective", "supportive", "tolerant"}
#     },

#     "3_praise_admiration_and_awe": {
#         "deep_reverence_and_awe": {"admiring", "amazed", "awed", "awestruck", "impressed"},
#         "verbal_praise_and_tribute": {"approving", "celebratory", "complimentary", "congratulatory", "laudatory", "respectful", "deferential"},
#         "gratitude_and_value": {"appreciative"}
#     },

#     "4_optimism_hope_and_inspiration": {
#         "forward_looking_confidence": {"bullish", "hopeful", "optimistic", "positive"},
#         "motivation_and_drive": {"encouraging", "exhortative", "inspired", "proactive", "promotional", "resilient"},
#         "devotional_hope": {"prayerful"}
#     },

#     "5_confidence_conviction_and_triumph": {
#         "strong_conviction": {"assertive", "confident", "convinced", "emphatic"},
#         "passion_and_fervor": {"effusive", "impassioned", "passionate", "patriotic"},
#         "pride_and_vindication": {"boastful", "proud", "triumphalist", "triumphant", "vindicated"}
#     },

#     "6_curiosity_and_intellectual_drive": {
#         "active_inquiry": {"curious", "inquisitive", "intrigued"},
#         "policy_and_technical_intellect": {"wonkish"}
#     },

#     "7_reassurance_harmony_and_satisfaction": {
#         "agreement_and_peace": {"affirmative", "agreeable", "conciliatory", "constructive"},
#         "making_amends": {"apologetic"},
#         "relief_and_trust": {"grateful", "reassured", "reassuring", "receptive", "relieved", "satisfied", "trusting", "understanding"}
#     },

#     "8_humor_playfulness_and_sincerity": {
#         "amusement_and_wit": {"amused", "humorous", "playful", "witty"},
#         "heartfelt_earnestness": {"earnest"}
#     }
# }

# # check to make sure all tones are accounted for in the hierarchical structure
# all_hierarchical_tones = set()
# for top_level, subgroups in HIERARCHICAL_POSITIVE_TONES.items():
#     for subgroup, tones in subgroups.items():
#         all_hierarchical_tones.update(tones)
# assert all_hierarchical_tones == POSITIVE, "Mismatch between hierarchical tones and POSITIVE set"

# NEUTRAL = {
#     "abrupt", "academic", "advisory", "analytical", "apathetic", "authoritarian",
#     "automated", "calming", "candid", "casual", "cautious", "certain",
#     "clinical", "colloquial", "concerned", "concise", "conditional", "coy",
#     "cryptic", "decisive", "determined", "directive", "explanatory", "factual",
#     "formal", "indifferent", "informal", "informative", "inquiring", "instructional",
#     "instructive", "journalistic", "laconic", "legalistic", "logical", "lukewarm",
#     "matter-of-fact", "measured", "mechanical", "neutral", "nonchalant", "objective",
#     "observational", "official", "patient", "pedantic", "pithy", "poetic",
#     "polite", "practical", "pragmatic", "predictive", "prescriptive", "prophetic", "prudent",
#     "puzzled", "realistic", "reflective", "reportorial", "restrained", "robotic",
#     "scientific", "sober", "sobering", "somber", "stern", "stoic",
#     "straightforward", "strategic", "succinct", "suggestive", "technical", "tentative",
#     "terse", "uncertain", "unclear", "unsurprised", "urgent", "utilitarian",
#     "vigilant", "watchful",
# }

# HIERARCHICAL_NEUTRAL_TONES = {
#     "1_objective_and_analytical": {
#         "pure_fact_and_logic": {"factual", "logical", "objective"},
#         "scientific_and_clinical": {"clinical", "scientific", "technical"},
#         "scholarly_analysis": {"academic", "analytical"},
#         "observational_neutrality": {"matter-of-fact", "neutral", "observational"},
#         "journalistic_reporting": {"journalistic", "reportorial"},
#         "informational_explanation": {"explanatory", "informative"}
#     },

#     "2_instructive_and_authoritative": {
#         "educational_instruction": {"instructional", "instructive"},
#         "advisory_recommendation": {"advisory", "suggestive"},
#         "normative_direction": {"prescriptive"},  # Standalone: dictates what SHOULD be done
#         "command_authority": {"authoritarian", "directive", "stern"},
#         "formal_protocol": {"formal", "legalistic", "official"},
#         "scholarly_rigidity": {"pedantic"}  # Standalone: rigid over-exactness
#     },

#     "3_brevity_and_directness": {
#         "concise_brevity": {"concise", "pithy", "succinct"},
#         "plain_directness": {"straightforward"},
#         "terse_economy": {"laconic", "terse"},
#         "jarring_suddenness": {"abrupt"},  # Standalone: sudden and curt
#         "open_frankness": {"candid"}  # Standalone: unfiltered honesty
#     },

#     "4_prudence_caution_and_strategy": {
#         "practical_utility": {"practical", "pragmatic", "realistic", "utilitarian"},
#         "cautious_restraint": {"cautious", "measured", "prudent", "restrained"},
#         "contingent_framing": {"conditional"},  # Standalone: depends on terms
#         "calculated_planning": {"strategic"},  # Standalone: forward-looking calculation
#         "tentative_hesitation": {"tentative", "uncertain"},
#         "lack_of_clarity": {"unclear"},
#         "alert_watchfulness": {"vigilant", "watchful"}
#     },

#     "5_conviction_resolve_and_urgency": {
#         "firm_resolve": {"certain", "decisive", "determined"},
#         "pressing_importance": {"urgent"},
#         "serious_gravity": {"sober", "somber"},
#         "reality_inducing_gravity": {"sobering"}  # Standalone: forces serious reflection
#     },

#     "6_detachment_stoicism_and_passivity": {
#         "flat_unconcern": {"apathetic", "indifferent"},
#         "half_heartedness": {"lukewarm"},
#         "unbothered_composure": {"nonchalant", "unsurprised"},
#         "enduring_composure": {"patient"},
#         "emotional_suppression": {"stoic"},
#         "impersonal_automation": {"automated", "mechanical", "robotic"}
#     },

#     "7_style_manner_and_mindset": {
#         "conversational_informality": {"casual", "colloquial", "informal"},
#         "courteous_etiquette": {"polite"},  # Standalone: respectful etiquette
#         "playful_evasiveness": {"coy"},  # Standalone: flirtatiously reserved
#         "obscure_enigma": {"cryptic"},  # Standalone: puzzlingly secret
#         "artistic_expression": {"poetic"},  # Standalone: lyrical/aesthetic style
#         "pensive_introspection": {"reflective"},  # Standalone: deep thoughtful self-examination
#         "active_querying": {"inquiring"},
#         "perplexed_confusion": {"puzzled"}
#     },

#     "8_composure_concern_and_foresight": {
#         "attentive_concern": {"concerned"},
#         "soothing_calm": {"calming"},
#         "future_projection": {"predictive", "prophetic"}
#     }
# }

# # check to make sure all tones are accounted for in the hierarchical structure
# all_hierarchical_tones = set()
# for top_level, subgroups in HIERARCHICAL_NEUTRAL_TONES.items():
#     for subgroup, tones in subgroups.items():
#         all_hierarchical_tones.update(tones)
# assert all_hierarchical_tones == NEUTRAL, "Mismatch between hierarchical tones and NEUTRAL set"

# MIXED = {
#     "adamant", "ambivalent", "anecdotal", "anticipatory", "astonished", "authoritative",
#     "bawdy", "bittersweet", "blunt", "chauvinistic", "clarifying", "commanding",
#     "conflicted", "crass", "diplomatic", "direct", "dogmatic", "dramatic",
#     "emotional", "envious", "forceful", "frank", "guarded", "hesitant",
#     "immature", "imperative", "imperious", "insistent", "jealous", "joking",
#     "melodramatic", "morbid", "motivational", "mystical", "nostalgic", "nuanced",
#     "opinionated", "partisan", "pastoral", "perplexed", "persuasive", "pleading",
#     "preachy", "punny", "radical", "resolute", "retrospective", "revolutionary",
#     "rhetorical", "smug", "speculative", "strict", "superstitious", "surprised",
#     "unapologetic", "visionary", "vulgar",
# }

# HIERARCHICAL_MIXED_TONES = {
#     "1_firmness_authority_and_conviction": {
#         "unyielding_resolve": {"adamant", "resolute", "unapologetic"},
#         "commanding_authority": {"authoritative", "commanding", "imperative", "imperious", "strict"},
#         "assertive_insistence": {"dogmatic", "forceful", "insistent", "opinionated"}
#     },

#     "2_uncertainty_conflict_and_hesitation": {
#         "internal_contradiction": {"ambivalent", "conflicted"},
#         "cautious_reserve": {"guarded", "hesitant"},
#         "hypothetical_conjecture": {"speculative"},  # Standalone: reasoning on incomplete evidence
#         "perplexed_bewildered": {"perplexed"}
#     },

#     "3_directness_candor_and_tact": {
#         "unfiltered_candor": {"blunt", "direct", "frank"},
#         "strategic_tact": {"diplomatic"},  # Standalone: navigating sensitive topics smoothly
#         "explanatory_precision": {"clarifying", "nuanced"}
#     },

#     "4_persuasion_rhetoric_and_vision": {
#         "inspirational_drive": {"motivational", "persuasive", "visionary"},
#         "ideological_zeal": {"preachy", "radical", "revolutionary"},
#         "stylistic_argumentation": {"rhetorical"}  # Standalone: framed for persuasion/effect
#     },

#     "5_surprise_emotion_and_drama": {
#         "sudden_wonder": {"astonished", "surprised"},
#         "heightened_theater": {"dramatic", "melodramatic"},
#         "raw_feeling": {"emotional"}
#     },

#     "6_reflection_nostalgia_and_spirituality": {
#         "looking_back": {"anecdotal", "bittersweet", "nostalgic", "retrospective"},
#         "looking_forward": {"anticipatory"},  # Standalone: eager or uneasy expectation
#         "transcendent_or_traditional": {"mystical", "pastoral", "superstitious"}
#     },

#     "7_irreverence_vulgarity_and_playfulness": {
#         "crude_or_coarse": {"bawdy", "crass", "vulgar"},
#         "childish_or_playful": {"immature", "joking", "punny"},
#         "dark_or_self_satisfied": {"morbid", "smug"}
#     },

#     "8_bias_desire_and_pleading": {
#         "sectional_bias": {"chauvinistic", "partisan"},
#         "possessive_desire": {"envious", "jealous"},
#         "earnest_entreaty": {"pleading"}  # Standalone: urgent emotional request
#     }
# }

# # check to make sure all tones are accounted for in the hierarchical structure
# all_hierarchical_tones = set()
# for top_level, subgroups in HIERARCHICAL_MIXED_TONES.items():
#     for subgroup, tones in subgroups.items():
#         all_hierarchical_tones.update(tones)
# assert all_hierarchical_tones == MIXED, "Mismatch between hierarchical tones and MIXED set"

# # now tones to remove before saving to json
# tones_to_remove = {'preachy', 'emotional', 'pastoral', 'doubtful', 'imperious', 'convinced', 'abrupt', 'unclear', 'inspired', 'grudging', 'opinionated', 'speechless', 'predictive', 'crude', 'forgiving', 'prejudiced', 'gracious', 'sober', 'pithy', 'revolutionary', 'prayerful', 'wonkish', 'overwhelmed', 'ranting', 'instructional', 'resilient', 'watchful', 'disparaging', 'bawdy', 'decisive', 'chauvinistic', 'automated', 'satisfied', 'poignant', 'silent', 'trusting'}

# all_dicts = [
#     HIERARCHICAL_NEGATIVE_TONES,
#     HIERARCHICAL_POSITIVE_TONES,
#     HIERARCHICAL_NEUTRAL_TONES,
#     HIERARCHICAL_MIXED_TONES,
# ]

# # Step 1: Discard tones from sets
# for tone in tones_to_remove:
#     for h_dict in all_dicts:
#         for top_level, subgroups in h_dict.items():
#             for subgroup, tones in subgroups.items():
#                 tones.discard(tone)

# # Step 2: Prune any subgroups that are now empty
# for h_dict in all_dicts:
#     for top_level, subgroups in h_dict.items():
#         empty_subgroups = [
#             subgroup for subgroup, tones in subgroups.items() if len(tones) == 0
#         ]
#         for empty_key in empty_subgroups:
#             del subgroups[empty_key]

# print(len(NEGATIVE), len(POSITIVE), len(NEUTRAL), len(MIXED))
# print("total tones:", len(NEGATIVE) + len(POSITIVE) + len(NEUTRAL) + len(MIXED))

# # dump the hierarchical sets to json (convert set to list first)
# def convert_to_dict_or_list(d):
#     if isinstance(d, dict):
#         return {k: convert_to_dict_or_list(v) for k, v in d.items()}
#     elif isinstance(d, set):
#         return list(d)
#     else:
#         print(f"Unexpected type {type(d)} for value {d}")
#         return d
    
# json_dict = {
#     "NEGATIVE": convert_to_dict_or_list(HIERARCHICAL_NEGATIVE_TONES),
#     "POSITIVE": convert_to_dict_or_list(HIERARCHICAL_POSITIVE_TONES),
#     "NEUTRAL": convert_to_dict_or_list(HIERARCHICAL_NEUTRAL_TONES),
#     "MIXED": convert_to_dict_or_list(HIERARCHICAL_MIXED_TONES)
# }

# # json.dump(json_dict, open("exp_data/tone_hierarchical_synonyms_corrected.json", "w"), indent=4)

### THEN WE HAD MORE ITERATIONS OF AI-ASSISTED IMPROVEMENT...

tones = json.load(open("exp_data/tone_hierarchical_synonyms.json", "r"))
print("total tones:", sum(len(tones[tone_type][top_level][subgroup]) for tone_type in tones for top_level in tones[tone_type] for subgroup in tones[tone_type][top_level]))
print("total synonyms:", sum(len(tones[tone_type][top_level].keys()) for tone_type in tones for top_level in tones[tone_type]))

