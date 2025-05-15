import json
import re
import os
from flask import Flask, request, render_template
import spacy

# --- Configuration ---
DATA_FOLDER = 'data'
LAWS_FILE = os.path.join(DATA_FOLDER, 'environmental_laws.json')
PRECEDENTS_FILE = os.path.join(DATA_FOLDER, 'environmental_precedents.json')
TOP_N_PRECEDENTS_DISPLAY = 3
TOP_N_LAWS_DISPLAY = 3
MIN_ABSOLUTE_KEYWORD_MATCHES_FOR_LAW = 2
MIN_PRIMARY_KEYWORD_MATCHES_FOR_LAW = 1

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Load spaCy English Model ---
nlp_spacy = None
try:
    nlp_spacy = spacy.load("en_core_web_sm")
    print("Successfully loaded spaCy 'en_core_web_sm' model.")
except Exception as e:
    print(f"ERROR loading spaCy model: {e}. Text processing may be affected.")
    print("Ensure 'en_core_web_sm' is downloaded: python -m spacy download en_core_web_sm")

# --- Load Local Laws & Precedents Data ---
laws_data = []
print(f"Attempting to load laws from: {os.path.abspath(LAWS_FILE)}")
try:
    with open(LAWS_FILE, 'r', encoding='utf-8') as f:
        raw_laws_data = json.load(f)
        for law_entry in raw_laws_data:
            if 'primary_keywords' in law_entry and isinstance(law_entry['primary_keywords'], list):
                law_entry['primary_keywords'] = [str(kw).lower().strip() for kw in law_entry['primary_keywords'] if str(kw).strip()]
            else: law_entry['primary_keywords'] = []
            if 'secondary_keywords' in law_entry and isinstance(law_entry['secondary_keywords'], list):
                law_entry['secondary_keywords'] = [str(kw).lower().strip() for kw in law_entry['secondary_keywords'] if str(kw).strip()]
            else: law_entry['secondary_keywords'] = []
        laws_data = raw_laws_data
    print(f"Successfully loaded and processed keywords for {len(laws_data)} law(s) from {LAWS_FILE}")
except Exception as e:
    laws_data = []
    print(f"ERROR loading/processing environmental laws: {e}")

precedents_data = []
print(f"Attempting to load precedents from: {os.path.abspath(PRECEDENTS_FILE)}")
try:
    with open(PRECEDENTS_FILE, 'r', encoding='utf-8') as f:
        raw_precedents_data = json.load(f)
        for precedent_entry in raw_precedents_data:
            if 'keywords' in precedent_entry and isinstance(precedent_entry['keywords'], list):
                precedent_entry['keywords'] = [str(kw).lower().strip() for kw in precedent_entry['keywords'] if str(kw).strip()]
            else: precedent_entry['keywords'] = []
            if 'tags' in precedent_entry and isinstance(precedent_entry['tags'], list):
                precedent_entry['tags'] = [str(kw).lower().strip() for kw in precedent_entry['tags'] if str(kw).strip()]
            else: precedent_entry['tags'] = []
        precedents_data = raw_precedents_data
    print(f"Successfully loaded and processed keywords for {len(precedents_data)} precedent(s) from {PRECEDENTS_FILE}")
except Exception as e:
    precedents_data = []
    print(f"ERROR loading/processing environmental precedents: {e}")

# --- Helper Functions ---
def preprocess_text_spacy(text):
    if not text or not nlp_spacy:
        if not nlp_spacy: print("DEBUG (preprocess_text_spacy): spaCy model not loaded.")
        return []
    doc = nlp_spacy(text.lower())
    lemmas = [token.lemma_ for token in doc if not token.is_punct and not token.is_stop and token.is_alpha]
    # print(f"DEBUG (preprocess_text_spacy): Input: '{text[:50]}...' -> Lemmas: {lemmas[:10]}...")
    return lemmas

def find_relevant_laws(summary_text):
    relevant_laws_all_matches = []
    if not summary_text or not laws_data or not nlp_spacy:
        if not laws_data and summary_text and nlp_spacy: print("DEBUG (find_relevant_laws): laws_data is empty.")
        return relevant_laws_all_matches

    summary_lemmas = preprocess_text_spacy(summary_text)
    summary_token_set = set(summary_lemmas)
    print(f"DEBUG (find_relevant_laws): Summary token set for matching: {summary_token_set}") # Keep this one

    if not summary_token_set:
        print("DEBUG (find_relevant_laws): Summary token set is empty after preprocessing.")
        return relevant_laws_all_matches

    for law_entry in laws_data:
        law_title = law_entry.get('title', 'Unknown Law')
        primary_kws_set = set(law_entry.get('primary_keywords', []))
        secondary_kws_set = set(law_entry.get('secondary_keywords', []))
        all_law_keywords_set = primary_kws_set.union(secondary_kws_set)
        
        common_primary_kws = summary_token_set.intersection(primary_kws_set)
        common_all_kws = summary_token_set.intersection(all_law_keywords_set)

        # *** ADDED/UNCOMMENTED THIS DEBUG PRINT ***
        print(f"\nDEBUG (find_relevant_laws): Comparing with Law: '{law_title}'")
        print(f"DEBUG (find_relevant_laws):   Its Primary Keywords: {primary_kws_set}")
        print(f"DEBUG (find_relevant_laws):   Its Secondary Keywords: {secondary_kws_set}")
        print(f"DEBUG (find_relevant_laws):   Common All: {common_all_kws}, Common Primary: {common_primary_kws}")
        # *** END OF ADDED/UNCOMMENTED DEBUG PRINT ***

        score = 0
        if common_all_kws:
            score = len(common_all_kws) + (len(common_primary_kws) * 2)

        if score > 0 and \
           len(common_all_kws) >= MIN_ABSOLUTE_KEYWORD_MATCHES_FOR_LAW and \
           (not primary_kws_set or len(common_primary_kws) >= MIN_PRIMARY_KEYWORD_MATCHES_FOR_LAW) :
            
            print(f"DEBUG (find_relevant_laws): ---> MATCH FOUND for Law '{law_title}'! Score: {score}, CommonAll Count: {len(common_all_kws)}, CommonPrimary Count: {len(common_primary_kws)}")
            
            section_ref = f"Section {law_entry.get('section', 'N/A')} of  {law_entry.get('act', 'N/A')}".strip()
            if law_entry.get('section', 'N/A').lower() == 'general' or \
               law_entry.get('section', 'N/A').lower() == 'general overview' or \
               not law_entry.get('section'):
                 section_ref = f" {law_entry.get('act', 'N/A')} (General Provisions)"
            elif not law_entry.get('act'):
                 section_ref = law_entry.get('title', 'Unknown Law Provision')

            law_info = {**law_entry, 'score': score, 'matched_keywords': list(common_all_kws), 'section_ref': section_ref}
            relevant_laws_all_matches.append(law_info)

    relevant_laws_all_matches.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    if not relevant_laws_all_matches:
        print("DEBUG (find_relevant_laws): No laws matched the refined criteria.")
    
    return relevant_laws_all_matches[:TOP_N_LAWS_DISPLAY]


def find_relevant_local_precedents(summary_text, identified_laws):
    # ... (this function can remain the same as the last version using Strategy 1) ...
    relevant_precedents = []
    if not summary_text or not precedents_data or not nlp_spacy:
        if not precedents_data and summary_text and nlp_spacy : print("DEBUG (find_relevant_local_precedents): Precedents data not loaded.")
        return relevant_precedents
    summary_lemmas = preprocess_text_spacy(summary_text)
    input_keywords_for_precedents = set(summary_lemmas)
    if not input_keywords_for_precedents:
        print("DEBUG (find_relevant_local_precedents): No keywords from summary to search precedents with.")
        return []
    scored_precedents = []
    for precedent_entry in precedents_data:
        precedent_kws = set(precedent_entry.get('keywords', []))
        precedent_tags = set(precedent_entry.get('tags', []))
        precedent_summary_lemmas_list = preprocess_text_spacy(precedent_entry.get('summary', ''))
        precedent_summary_lemmas = set(precedent_summary_lemmas_list) if precedent_summary_lemmas_list else set()
        searchable_precedent_terms = precedent_kws.union(precedent_tags).union(precedent_summary_lemmas)
        common_terms = input_keywords_for_precedents.intersection(searchable_precedent_terms)
        score = len(common_terms)
        if score > 0:
            scored_precedents.append({**precedent_entry, 'score': score, 'source': 'Local DB'})
    scored_precedents.sort(key=lambda x: x.get('score', 0), reverse=True)
    return scored_precedents[:TOP_N_PRECEDENTS_DISPLAY]


# --- Flask Routes ---
@app.route('/', methods=['GET'])
def index():
    spacy_model_is_loaded = bool(nlp_spacy)
    return render_template('index.html',
                           analysis=None,
                           spacy_model_loaded=spacy_model_is_loaded,
                           show_results=False)

@app.route('/analyze', methods=['POST'])
def analyze():
    case_summary = request.form.get('case_summary_input', '')
    spacy_model_is_loaded = bool(nlp_spacy)
    analysis_results = {
        'laws': [], 'precedents': [], 'input_summary': case_summary,
        'error': None, 'spacy_error': None
    }
    should_show_results_section = True 

    if not spacy_model_is_loaded:
        analysis_results['spacy_error'] = "spaCy NLP model could not be loaded. Text processing and analysis are disabled."
    if not case_summary.strip():
        analysis_results['error'] = "Case summary input was empty."
    
    if spacy_model_is_loaded and case_summary.strip():
        print("\n--- Starting Analysis ---")
        identified_laws = find_relevant_laws(case_summary)
        analysis_results['laws'] = identified_laws
        print(f"DEBUG (analyze): Identified Top Laws ({len(identified_laws)}): {[(law.get('section_ref', law.get('title')), law.get('score')) for law in identified_laws]}")

        analysis_results['precedents'] = find_relevant_local_precedents(case_summary, identified_laws)
        print(f"DEBUG (analyze): Identified Top Precedents ({len(analysis_results['precedents'])}): {[(p.get('citation'), p.get('score')) for p in analysis_results['precedents']]}")
        print("--- Analysis Finished ---\n")
    
    return render_template('index.html',
                           analysis=analysis_results,
                           spacy_model_loaded=spacy_model_is_loaded,
                           show_results=should_show_results_section)

# --- Run the App ---
if __name__ == '__main__':
    if not nlp_spacy: print("\n*** ERROR: spaCy model failed to load! Check download. ***\n")
    if not laws_data: print("\n*** WARNING: Laws data (environmental_laws.json) not loaded or empty! Check file and content. ***\n")
    if not precedents_data: print("\n*** WARNING: Precedents data (environmental_precedents.json) not loaded or empty! Check file and content. ***\n")
    app.run(debug=True, use_reloader=False)