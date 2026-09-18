"""
ORCA_NLP main application.

Pipeline:

1. Detect language
2. Translate query into English
3. Classify intent
4. Expand marine glossary terms
5. Retrieve relevant context
6. Generate an English answer
7. Translate the answer into the user's language
"""

from nlp.llm.groq_client import (
    synthesize_marine_response,
    clean_rag_leakage,
)

from nlp.detection.language_detector import detect_language
from nlp.detection.intent_classifier import classify_intent

from nlp.rag.rag_pipeline import get_relevant_context

from nlp.translation.marine_glossary import expand_terms
from nlp.translation.translator import (
    translate_to_english,
    translate_response,
)


def get_language_code(language_result) -> str:
    """
    Extract the language code from the language detector result.
    """

    if isinstance(language_result, str):
        language = language_result.strip().lower()

        if language:
            return language

        return "en"

    if isinstance(language_result, dict):
        language = (
            language_result.get("language_code")
            or language_result.get("language")
            or language_result.get("lang")
            or language_result.get("code")
        )

        if isinstance(language, str):
            language = language.strip().lower()

            if language:
                return language

    return "en"


def detect_hinglish(query: str) -> bool:
    """
    Detect Hindi written using English letters.

    Examples:
        pfz kya hai
        mausam kaisa hai
        mujhe samjhao
    """

    if not isinstance(query, str):
        return False

    query_lower = query.lower().strip()

    hinglish_words = {
        "kya",
        "hai",
        "hain",
        "kaise",
        "kaisa",
        "kaisi",
        "kyun",
        "kyon",
        "kab",
        "kahan",
        "kahaan",
        "ka",
        "ke",
        "ki",
        "ko",
        "mein",
        "me",
        "se",
        "par",
        "aur",
        "ya",
        "mujhe",
        "mujhko",
        "batao",
        "bataiye",
        "samjhao",
        "samjhaiye",
        "chahiye",
        "paani",
        "pani",
        "machhli",
        "machli",
        "mausam",
        "samundar",
        "samandar",
        "samudra",
        "lehar",
        "lahrein",
        "hawa",
        "baarish",
        "barish",
        "toofan",
        "tufan",
        "cyclone",
    }

    words = query_lower.split()

    for word in words:
        cleaned_word = word.strip("?!.,:;()[]{}\"'")

        if cleaned_word in hinglish_words:
            return True

    return False


def detect_manglish(query: str) -> bool:
    """
    Detect Malayalam written using English letters (Manglish).

    Examples:
        pfz enthaanu
        meen evide kittum
        kadal kshobham
        mazha undaakumo
    """
    if not isinstance(query, str):
        return False

    query_lower = query.lower().strip()

    manglish_words = {
        "enthaanu",
        "enthanu",
        "enth",
        "entha",
        "engane",
        "enganeyanu",
        "evide",
        "evideyannu",
        "kittum",
        "kittan",
        "meen",
        "matsyam",
        "kadal",
        "kadalo",
        "kadalin",
        "mazha",
        "kaatu",
        "kaattu",
        "kaat",
        "theeram",
        "choodu",
        "thiramaala",
        "thiramaalakal",
        "rakshikku",
        "sahayam",
        "ariyaan",
        "ariyuka",
        "neram",
        "kooduthal",
        "kuravu",
        "choodundo",
        "undundo",
        "undaakumo",
        "undakumo",
        "nalla",
        "mosham",
        "surakshitham",
    }

    words = query_lower.split()

    for word in words:
        cleaned_word = word.strip("?!.,:;()[]{}\"'")

        if cleaned_word in manglish_words:
            return True

    return False


def detect_alert_type(query: str) -> str | None:
    """
    Detect safety-related marine weather alerts.

    Supports English and common Hindi phrases.
    """

    if not isinstance(query, str):
        return None

    query_lower = query.lower().strip()

    # Strong wind warning
    strong_wind_phrases = [
        "strong wind",
        "strong winds",
        "high wind",
        "high winds",
        "heavy wind",
        "heavy winds",

        # Hindi
        "तेज़ हवा",
        "तेज हवा",
        "तेज़ हवाएं",
        "तेज हवाएं",
        "तेज़ हवाएँ",
        "तेज हवाएँ",
        "हवा तेज",
        "हवा तेज़",
    ]

    if any(
        phrase in query_lower
        for phrase in strong_wind_phrases
    ):
        return "strong_wind_warning"

    # High wave warning
    high_wave_phrases = [
        "high wave",
        "high waves",
        "large wave",
        "large waves",
        "rough sea",
        "rough seas",

        # Hindi
        "ऊंची लहरें",
        "ऊँची लहरें",
        "लहरें ऊंची",
        "लहरें ऊँची",
    ]

    if any(
        phrase in query_lower
        for phrase in high_wave_phrases
    ):
        return "high_wave_warning"

    # Cyclone warning
    cyclone_phrases = [
        "cyclone",
        "cyclone warning",
        "storm warning",
        "tropical storm",

        # Hindi
        "चक्रवात",
        "चक्रवात चेतावनी",
        "तूफान",
        "तूफ़ान",
        "तूफान की चेतावनी",
        "तूफ़ान की चेतावनी",
    ]

    if any(
        phrase in query_lower
        for phrase in cyclone_phrases
    ):
        return "cyclone_warning"

    # Unsafe weather warning
    unsafe_weather_phrases = [
        "unsafe weather",
        "bad weather",
        "severe weather",
        "dangerous weather",

        # Hindi
        "खराब मौसम",
        "ख़राब मौसम",
        "खतरनाक मौसम",
        "ख़तरनाक मौसम",
        "मौसम खराब",
        "मौसम ख़राब",
    ]

    if any(
        phrase in query_lower
        for phrase in unsafe_weather_phrases
    ):
        return "unsafe_weather_warning"

    # Return to shore warning
    return_to_shore_phrases = [
        "return to shore",
        "go back to shore",
        "move to shore",
        "safe harbor",
        "safe harbour",
        "nearest safe harbor",
        "nearest safe harbour",

        # Hindi
        "किनारे लौटें",
        "किनारे वापस जाएं",
        "किनारे वापस जाएँ",
        "समुद्र से वापस आएं",
        "समुद्र से वापस आएँ",
        "सुरक्षित बंदरगाह",
    ]

    if any(
        phrase in query_lower
        for phrase in return_to_shore_phrases
    ):
        return "return_to_shore"

    return None


def create_alert_answer(alert_type: str) -> str:
    """
    Create an English answer for a marine safety alert.
    """

    alert_answers = {
        "strong_wind_warning": (
            "⚠️ STRONG WIND WARNING\n\n"
            "Strong winds can affect boat stability and navigation.\n"
            "Check wind-speed forecasts before going to sea.\n"
            "Small boats should avoid unsafe weather conditions."
        ),

        "high_wave_warning": (
            "⚠️ HIGH WAVE WARNING\n\n"
            "High waves can make marine travel dangerous.\n"
            "Small boats should avoid going to sea during high waves.\n"
            "Check wave-height forecasts and move to a safe harbor "
            "if conditions worsen."
        ),

        "cyclone_warning": (
            "⚠️ CYCLONE WARNING\n\n"
            "Cyclone conditions can be extremely dangerous for fishermen.\n"
            "Do not go to sea during cyclone warnings.\n"
            "Follow official weather advisories and move to a safe harbor."
        ),

        "unsafe_weather_warning": (
            "⚠️ UNSAFE WEATHER WARNING\n\n"
            "Weather conditions may be dangerous for marine travel.\n"
            "Check forecasts for wind, waves, rainfall, and cyclone warnings.\n"
            "If conditions worsen, return to shore or move to a safe harbor."
        ),

        "return_to_shore": (
            "⚠️ SAFETY ALERT\n\n"
            "Sea conditions may be dangerous.\n"
            "Return to shore immediately or move to the nearest safe harbor.\n"
            "Follow official marine safety warnings."
        ),
    }

    return alert_answers.get(
        alert_type,
        "Please follow official marine safety advisories.",
    )


def is_definition_query(query: str) -> bool:
    """Check if query is asking for a definition or explanation."""
    q = query.lower()
    def_markers = [
        "what is", "what are", "what's", "explain", "meaning", "define", "definition",
        "tell me about", "kya hai", "kya h", "kya hota", "samjhao", "batao", "kise kehte",
        "kaisa hota", "aratham", "matlab", "meaning of", "info on", "information about",
        "terms", "guidelines", "safety tips", "rules", "rule", "regulations",
        "എന്താണ്", "അർത്ഥം", "വിശദീകരിക്കുക", "എന്താണ് ഉദ്ദേശിക്കുന്നത്",
        "क्या है", "क्या होता है", "बताओ", "समझाओ", "अर्थ", "नियम",
        "என்ன", "விளக்கு", "பொருள்", "ఏమిటి", "వివరించు"
    ]
    return any(marker in q for marker in def_markers)

def detect_response_key(
    query: str,
    intent_result,
) -> str:
    """
    Detect the type of response required.
    Only returns definition keys when the user is explicitly asking for meaning/definition.
    """
    alert_type = detect_alert_type(query)
    if alert_type is not None:
        return alert_type

    query_lower = query.lower()
    is_def = is_definition_query(query_lower)

    if is_def:
        if "pfz" in query_lower or "fishing zone" in query_lower or "potential fishing" in query_lower:
            return "pfz"
        if "sst" in query_lower or "sea surface temperature" in query_lower or "temperature" in query_lower:
            return "sst"
        if "imbl" in query_lower or "international maritime boundary" in query_lower or "boundary" in query_lower:
            return "imbl"

    # Intent-based fallback
    if isinstance(intent_result, dict):
        intent = intent_result.get("intent", "")
        if isinstance(intent, str):
            intent = intent.upper().strip()
            if intent == "WEATHER_FORECAST":
                return "weather_forecast"
            if intent == "SAFETY_CHECK":
                return "safety_check"

    return "unknown"


def create_clean_answer(
    query: str,
    intent_result,
    context,
) -> str:
    """
    Create a clean, natural fisherman-friendly English answer
    using intent and retrieved knowledge context without leaking metadata.
    """
    # 1. Handle safety alerts first
    alert_type = detect_alert_type(query)
    if alert_type is not None:
        return create_alert_answer(alert_type)

    intent_name = "TERMINOLOGY_EXPLANATION"
    if isinstance(intent_result, dict):
        intent_name = intent_result.get("intent", "TERMINOLOGY_EXPLANATION")
    elif isinstance(intent_result, str):
        intent_name = intent_result

    # 2. Extract clean factual snippets (no metadata headers)
    facts = []
    if isinstance(context, dict):
        docs = context.get("documents", [])
        for doc in docs:
            if isinstance(doc, dict) and doc.get("text"):
                facts.append(doc["text"].strip())
        if not facts and context.get("context"):
            facts.append(context["context"].strip())
    elif isinstance(context, list):
        for item in context:
            if isinstance(item, dict) and item.get("text"):
                facts.append(item["text"].strip())
            elif isinstance(item, str):
                facts.append(item.strip())
    elif isinstance(context, str) and context.strip():
        facts.append(context.strip())

    # 3. Synthesize natural marine answer
    raw_answer = synthesize_marine_response(
        query=query,
        context_facts=facts,
        intent=intent_name,
    )

    # 4. Strict guardrail against metadata or chunk ID leakage
    cleaned_answer = clean_rag_leakage(raw_answer)
    return cleaned_answer
def extract_evidence(context) -> dict:
    """
    Extract user-facing evidence information from RAG context.

    Supports the dictionary structure returned by get_relevant_context().
    """

    evidence = {
        "sources": [],
        "chunks": [],
    }

    if not context:
        return evidence

    # Expected RAG structure:
    # {
    #     "query": ...,
    #     "documents": [...],
    #     "context": "..."
    # }
    if isinstance(context, dict):
        documents = context.get("documents", [])

        if isinstance(documents, list):
            for document in documents:
                if isinstance(document, dict):
                    source = (
                        document.get("source")
                        or document.get("file")
                        or document.get("filename")
                    )

                    section = document.get("section")
                    chunk_id = (
                        document.get("chunk_id")
                        or document.get("chunk")
                        or document.get("id")
                    )

                    if source:
                        source = str(source).strip()

                        if source and source not in evidence["sources"]:
                            evidence["sources"].append(source)

                    chunk_info = {}

                    if source:
                        chunk_info["source"] = source

                    if section:
                        chunk_info["section"] = str(section)

                    if chunk_id is not None:
                        chunk_info["chunk_id"] = str(chunk_id)

                    if chunk_info:
                        evidence["chunks"].append(chunk_info)

                elif isinstance(document, str):
                    document = document.strip()

                    if document and document not in evidence["sources"]:
                        evidence["sources"].append(document)

        return evidence

    # Support a list-based context as well.
    if isinstance(context, list):
        for item in context:
            if isinstance(item, dict):
                source = (
                    item.get("source")
                    or item.get("file")
                    or item.get("filename")
                )

                if source:
                    source = str(source).strip()

                    if source and source not in evidence["sources"]:
                        evidence["sources"].append(source)

            elif isinstance(item, str):
                item = item.strip()

                if item and item not in evidence["sources"]:
                    evidence["sources"].append(item)

    return evidence

def process_query(query: str) -> dict:
    """
    Run the complete ORCA NLP pipeline.
    """

    if not isinstance(query, str):
        raise TypeError("query must be a string")

    if not query.strip():
        raise ValueError("query cannot be empty")

    # 1. Detect language
    language_result = detect_language(query)
    language = get_language_code(language_result)

    # Detect Hindi or Malayalam written using English letters.
    # Example: "pfz kya hai?" -> hi, "pfz enthaanu?" -> ml
    if detect_hinglish(query):
        language = "hi"
    elif detect_manglish(query):
        language = "ml"

    print("Detected language result:", language_result)
    print("Detected language code:", language)

    # 2. Translate the query into English
    english_query = translate_to_english(query)

    # 3. Classify intent
    intent_result = classify_intent(english_query)

    # 4. Expand marine glossary terms
    expanded_query = expand_terms(english_query)

    # 5. Retrieve relevant context facts
    context = get_relevant_context(expanded_query)

    # 6. Create English synthesized answer
    english_answer = create_clean_answer(
        expanded_query,
        intent_result,
        context,
    )

    # 7. Translate answer into the user's language
    final_answer = translate_response(
        english_answer,
        language,
    )
    final_answer = clean_rag_leakage(final_answer)
    evidence = extract_evidence(context)

    return {
        "query": query,
        "english_query": english_query,
        "expanded_query": expanded_query,
        "language": language_result,
        "language_code": language,
        "intent": intent_result,
        "context": context,
        "english_answer": english_answer,
        "answer": final_answer,
        "sources": evidence["sources"],
        "evidence": evidence,
    }


def print_result(result: dict) -> None:
    """
    Print the result in a readable format.
    """

    print("\nLanguage:")
    print(result["language"])

    print("\nLanguage code:")
    print(result["language_code"])

    print("\nIntent:")
    print(result["intent"])

    print("\nExpanded query:")
    print(result["expanded_query"])

    print("\nResponse:")
    print(result["answer"])

    print("\nEvidence / Sources:")

    sources = result.get("sources", [])

    if sources:
        for index, source in enumerate(sources, start=1):
            print(f"{index}. {source}")
    else:
        print("No specific RAG source was retrieved.")


def main() -> None:
    """
    Run the ORCA NLP command-line application.
    """

    print("ORCA NLP Demo")
    print("Type 'exit' to stop.")

    while True:
        try:
            query = input("\nYou: ").strip()

            if query.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break

            if not query:
                print("Please enter a question.")
                continue

            result = process_query(query)
            print_result(result)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

        except Exception as error:
            print(f"\nError: {error}")


if __name__ == "__main__":
    main()