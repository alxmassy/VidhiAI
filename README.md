# VidhiAI - AI-Powered Law Assistant

[![Watch the Demo](https://img.youtube.com/vi/FTjgbdYyV84/hqdefault.jpg)](https://www.youtube.com/watch?v=FTjgbdYyV84)

VidhiAI is a prototype web application designed to assist legal professionals by analyzing case summaries related to Indian environmental law and suggesting potentially applicable laws and relevant precedents.

## Features
*   **Input Case Summary:** Users can input a textual summary of an environmental case.
*   **NLP Processing:** Uses spaCy for lemmatization and stopword removal from the input.
*   **Relevant Law Identification:** Matches processed input against a curated local database (`environmental_laws.json`) of key environmental acts and rules to suggest applicable provisions.
*   **Precedent Suggestion:** Searches a local database (`environmental_precedents.json`) for relevant case law based on keywords from the input summary.
*   **User Interface:** Built with Flask and a simple Bootstrap-styled frontend.

## Tech Stack
*   **Backend:** Python, Flask
*   **NLP:** spaCy
*   **Data:** JSON files for laws and precedents
*   **Frontend:** HTML, CSS (Bootstrap 5)
