# finder.py (Definitive Final Version)
import pandas as pd
import re

def normalize_text(text):
    """Converts to lowercase and removes non-alphanumeric characters for matching."""
    if not isinstance(text, str):
        return ""
    # Keep spaces to separate words
    text = re.sub(r'[^a-z0-9\s]', '', text.lower())
    return re.sub(r'\s+', ' ', text).strip()

def find_best_templates(query, templates_df, profiles_df, search_index, top_n=20):
    """
    Finds and ranks templates using a corrected, robust method for context detection.
    """
    if not query.strip():
        return []

    query_keywords = set(normalize_text(query).split())
    
    # --- Step 1: CORRECTED Intelligent Context Detection ---
    primary_context = None
    context_keywords = set()
    general_query_keywords = set(query_keywords)

    # Search for a match across ALL relevant profile columns
    for _, profile_row in profiles_df.iterrows():
        # Combine all text from the profile row into one searchable set
        profile_text_to_search = []
        for col in ['client_type', 'keywords', 'industry', 'business_niche', 'marketing_focus', 'relevant_keywords']:
            profile_text_to_search.append(str(profile_row.get(col, '')))
        
        profile_words = set(normalize_text(' '.join(profile_text_to_search)).split())

        # If there's an intersection, we've found our context!
        if query_keywords.intersection(profile_words):
            primary_context = profile_row['client_type']
            context_keywords = profile_words # Use all words from this profile as context
            general_query_keywords = query_keywords - context_keywords
            break # Stop after finding the first matching profile

    # --- Step 2: Broad Candidate Selection ---
    # Use both query and discovered context keywords to find candidates
    all_search_terms = query_keywords.union(context_keywords)
    candidate_indices = set()
    for keyword in all_search_terms:
        candidate_indices.update(search_index.get(keyword, []))

    if not candidate_indices:
        return []

    # --- Step 3: Score ONLY the Candidate Templates ---
    scores = []
    for index in candidate_indices:
        row = templates_df.loc[index]
        template_words = set(row.get('searchable_text', '').split())
        reasons = []
        
        # Context Score (Highest Priority)
        context_matches = context_keywords.intersection(template_words)
        context_score = len(context_matches) * 20
        if context_matches and primary_context:
            reasons.append(f"Matches **{primary_context}** profile (e.g., '{list(context_matches)[0]}')")

        # Direct Query Score
        direct_matches = general_query_keywords.intersection(template_words)
        direct_score = len(direct_matches) * 10
        if direct_matches:
            reasons.append(f"Matches query term: '{list(direct_matches)[0]}'")

        relevance_score = context_score + direct_score
        
        if relevance_score == 0:
            continue

        try: performance_score = float(str(row.get('avg_ctr', '0')).replace('%', ''))
        except: performance_score = 0
        
        final_score = (0.90 * relevance_score) + (0.10 * performance_score)
        scores.append({'score': final_score, 'data': row})

    # De-duplicate results
    unique_results = []
    seen_templates = set()
    for result in sorted(scores, key=lambda x: x['score'], reverse=True):
        if result['data']['template_name'] not in seen_templates:
            unique_results.append(result)
            seen_templates.add(result['data']['template_name'])

    return unique_results[:top_n]