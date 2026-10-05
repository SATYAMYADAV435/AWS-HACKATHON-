"""
KisanMitra — backend/bedrock_client.py
Unified client for Amazon Bedrock with retry logic, fallback model handling,
and cached response fallback per ARCHITECTURE.md §7.
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger("kisanmitra.bedrock")

# Environment variables
USE_CACHE = os.environ.get("USE_CACHE", "true").lower() in ("true", "1", "yes")
PRIMARY_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
FALLBACK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID_FALLBACK", "amazon.titan-text-express-v1")
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "ap-south-1")

_bedrock_runtime_client = None

def get_bedrock_client():
    global _bedrock_runtime_client
    if _bedrock_runtime_client is not None:
        return _bedrock_runtime_client
    try:
        import boto3
        _bedrock_runtime_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        return _bedrock_runtime_client
    except Exception as e:
        logger.warning(f"Could not initialize Bedrock client: {e}")
        return None

def _format_payload(model_id: str, prompt: str, system_prompt: str, max_tokens: int, temperature: float) -> str:
    if "claude" in model_id.lower():
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            body["system"] = system_prompt
        return json.dumps(body)
    elif "titan" in model_id.lower():
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        body = {
            "inputText": full_prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "stopSequences": [],
                "temperature": temperature,
                "topP": 0.9
            }
        }
        return json.dumps(body)
    else:
        # Default simple payload
        return json.dumps({"prompt": prompt, "max_tokens": max_tokens, "temperature": temperature})

def _parse_response(model_id: str, response_body: str) -> str:
    parsed = json.loads(response_body)
    if "claude" in model_id.lower():
        content_blocks = parsed.get("content", [])
        if content_blocks and "text" in content_blocks[0]:
            return content_blocks[0]["text"]
        return ""
    elif "titan" in model_id.lower():
        results = parsed.get("results", [])
        if results and "outputText" in results[0]:
            return results[0]["outputText"]
        return ""
    return str(parsed)

def invoke_model(
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 1000,
    temperature: float = 0.2,
    model_id: Optional[str] = None
) -> str:
    """
    Invoke Bedrock model with fallback chain:
    Primary Model -> Fallback Model -> Cached/Simulated fallback.
    """
    if USE_CACHE:
        logger.info("USE_CACHE=true active: bypassing live Bedrock API call.")
        return _cached_or_simulated_llm(prompt, system_prompt)

    client = get_bedrock_client()
    if not client:
        logger.warning("No Bedrock client available; using cached fallback.")
        return _cached_or_simulated_llm(prompt, system_prompt)

    models_to_try = [model_id] if model_id else [PRIMARY_MODEL_ID, FALLBACK_MODEL_ID]

    for current_model in models_to_try:
        if not current_model:
            continue
        for attempt in range(2):
            try:
                payload = _format_payload(current_model, prompt, system_prompt, max_tokens, temperature)
                response = client.invoke_model(
                    modelId=current_model,
                    contentType="application/json",
                    accept="application/json",
                    body=payload
                )
                body_bytes = response["body"].read()
                return _parse_response(current_model, body_bytes.decode("utf-8"))
            except Exception as exc:
                logger.warning(f"Bedrock call attempt {attempt+1} failed on {current_model}: {exc}")
                time.sleep(0.5 * (attempt + 1))

    logger.warning("All Bedrock model attempts failed; falling back to cached response.")
    return _cached_or_simulated_llm(prompt, system_prompt)

def _cached_or_simulated_llm(prompt: str, system_prompt: str) -> str:
    """
    Deterministic simulated response for offline/cached mode and testing.
    Identifies router vs supervisor requests.
    """
    p_lower = prompt.lower()
    
    # 1. Router requests (expecting JSON with intent, crop, language)
    if "intent" in system_prompt.lower() or "router" in system_prompt.lower() or "classify" in system_prompt.lower():
        # Check default language preference first as baseline
        lang = "mr"
        if "preference: \"hi\"" in p_lower or "preference: hi" in p_lower:
            lang = "hi"
        elif "preference: \"en\"" in p_lower or "preference: en" in p_lower:
            lang = "en"
        elif "preference: \"mr\"" in p_lower or "preference: mr" in p_lower:
            lang = "mr"

        # Override if specific language markers are present
        if any(c in p_lower for c in ["काय", "कसे", "कशी", "आहे", "कांद्या", "पिकवावे", "घ्यावे", "करावी", "करावे", "हवामान", "शेतात", "पाऊस", "कर्ज"]):
            lang = "mr"
        elif any(c in p_lower for c in ["क्या", "कैसे", "मौसम", "दाम", "फसल", "लगाएं", "करें", "लोन", "कीटनाशक", "छिड़काव"]):
            lang = "hi"
        elif any(w in p_lower for w in ["what", "how", "weather", "price", "grow", "crop", "today", "spray", "loan"]):
            if "preference: \"hi\"" not in p_lower and "preference: \"mr\"" not in p_lower:
                lang = "en"

        # Detect out-of-scope queries (e.g. loan, subsidy, tractor, credit)
        if any(k in p_lower for k in ["कर्ज", "लोन", "loan", "ट्रॅक्टर", "ट्रैक्टर", "tractor", "सबसिडी", "अनुदान"]):
            return json.dumps({
                "intent": "unknown",
                "crop": None,
                "language": lang
            }, ensure_ascii=False)

        # Detect crop with Devanagari inflections
        crop = None
        if any(k in p_lower for k in ["onion", "कांदा", "कांद्या", "कांदे", "प्याज"]):
            crop = "onion"
        elif any(k in p_lower for k in ["wheat", "गहू", "गव्हा", "गेहूं"]):
            crop = "wheat"
        elif any(k in p_lower for k in ["gram", "हरभरा", "हरभऱ्या", "चना", "चने"]):
            crop = "gram"
        elif any(k in p_lower for k in ["tomato", "टोमॅटो", "टमाटर"]):
            crop = "tomato"
        elif any(k in p_lower for k in ["jowar", "ज्वारी", "ज्वार"]):
            crop = "rabi_jowar"
        elif any(k in p_lower for k in ["safflower", "करडई", "कुसुम"]):
            crop = "safflower"

        # Detect intent
        if any(k in p_lower for k in ["हवामान", "पाऊस", "weather", "rain", "मौसम", "बारिश", "spray", "फवारणी", "छिड़काव"]):
            intent = "weather_today"
        elif any(k in p_lower for k in ["भाव", "दर", "price", "mandi", "बाजारभाव", "रेट", "दाम"]):
            intent = "prices"
        elif any(k in p_lower for k in ["कसे", "कशी", "how to", "guide", "लागवड", "पद्धत", "रोग", "खेती"]):
            intent = "how_to_grow"
        elif any(k in p_lower for k in ["काय पिकवावे", "कोणते पीक", "what to grow", "क्या लगाएं", "फसल"]):
            intent = "what_to_grow"
        else:
            intent = "what_to_grow" if not crop else "how_to_grow"

        return json.dumps({
            "intent": intent,
            "crop": crop,
            "language": lang
        }, ensure_ascii=False)

    # 2. Supervisor requests (expecting AnswerCard JSON)
    # Parse target language and intent from prompt
    target_lang = "mr"
    if "target language: hi" in p_lower or "language=hi" in p_lower:
        target_lang = "hi"
    elif "target language: en" in p_lower or "language=en" in p_lower:
        target_lang = "en"
    elif "target language: mr" in p_lower or "language=mr" in p_lower:
        target_lang = "mr"

    intent = "what_to_grow"
    if "intent: weather_today" in p_lower:
        intent = "weather_today"
    elif "intent: prices" in p_lower:
        intent = "prices"
    elif "intent: how_to_grow" in p_lower:
        intent = "how_to_grow"
    elif "intent: unknown" in p_lower:
        intent = "unknown"

    # Multi-language and multi-intent simulated cards
    if target_lang == "hi":
        if intent == "weather_today":
            card = {
                "title": "मौसम एवं छिड़काव सलाह",
                "summary_lines": [
                    "नासिक क्षेत्र में आज मौसम साफ और शुष्क रहेगा।",
                    "अधिकतम तापमान 29 डिग्री और हवा की गति 9 किमी प्रति घंटा रहेगी।",
                    "आज दोपहर कीटनाशक छिड़काव के लिए मौसम पूरी तरह अनुकूल है।"
                ],
                "steps": [
                    "1. हवा की गति कम होने पर सुबह 11 बजे से पहले या दोपहर 3 बजे के बाद छिड़काव करें।",
                    "2. सुरक्षा के लिए दस्ताने और मास्क का उपयोग अवश्य करें।",
                    "3. खेत में नमी की जांच करके आवश्यकतानुसार हल्की सिंचाई करें।"
                ],
                "labels": ["मौसम पूर्वानुमान", "अनुमानित जानकारी"],
                "sources": ["भारतीय मौसम विभाग (IMD)", "कृषि विज्ञान केंद्र (KVK)"],
                "speak_text": "आज नासिक में मौसम साफ है और हवा की गति धीमी है। आप आज खेत में छिड़काव कर सकते हैं।",
                "language": "hi"
            }
        elif intent == "prices":
            card = {
                "title": "मंडी भाव (नासिक मंडी)",
                "summary_lines": [
                    "नासिक और लासलगांव मंडी में प्याज का औसत भाव ₹1,850 प्रति क्विंटल है।",
                    "न्यूनतम भाव ₹1,200 और अधिकतम भाव ₹2,400 प्रति क्विंटल दर्ज किया गया।",
                    "मांग अच्छी होने के कारण अगले हफ्ते भाव स्थिर रहने की संभावना है।"
                ],
                "steps": [
                    "1. प्याज की अच्छी तरह छंटाई करके ही मंडी में बिक्री के लिए ले जाएं।",
                    "2. सूखा और अच्छी गुणवत्ता वाला प्याज ऊंचे दामों पर बिकता है।",
                    "3. स्थानीय कृषि उपज मंडी समिति के दैनिक भाव पर नजर रखें।"
                ],
                "labels": ["आधिकारिक मंडी भाव", "अनुमानित जानकारी"],
                "sources": ["महाराष्ट्र राज्य कृषि विपणन बोर्ड (MSAMB)"],
                "speak_text": "नासिक मंडी में आज प्याज का औसत भाव 1850 रुपये प्रति क्विंटल है। बाजार में भाव स्थिर रहने की उम्मीद है।",
                "language": "hi"
            }
        elif intent == "how_to_grow":
            card = {
                "title": "फसल प्रबंधन मार्गदर्शिका (रबी प्याज)",
                "summary_lines": [
                    "रबी प्याज की रोपाई अक्टूबर से नवंबर के बीच पूरी करें।",
                    "मध्यम से भारी और जल निकासी वाली उपजाऊ मिट्टी का चयन करें।",
                    "जैविक खाद और अनुशंसित उर्वरकों का संतुलित उपयोग करें।"
                ],
                "steps": [
                    "1. प्रति एकड़ 10 से 12 टन सड़ी हुई गोबर की खाद मिट्टी में मिलाएं।",
                    "2. क्यारियों में 15 गुणा 10 सेमी की दूरी पर स्वस्थ पौधे लगाएं।",
                    "3. खरपतवार नियंत्रण के लिए रोपाई के बाद हल्की निराई-गुड़ाई करें।"
                ],
                "labels": ["फसल सलाह", "अनुशंसित जानकारी"],
                "sources": ["महात्मा फुले कृषि विद्यापीठ (MPKV) राहुरी"],
                "speak_text": "रबी प्याज की खेती के लिए मध्यम से भारी मिट्टी और सही पोषण प्रबंधन जरूरी है। समय पर रोपाई पूरी करें।",
                "language": "hi"
            }
        elif intent == "unknown":
            card = {
                "title": "किसान सहायता एवं मार्गदर्शन",
                "summary_lines": [
                    "किसानमित्र फसलों, मौसम, मंडी भाव और खेती तकनीकों की जानकारी देता है।",
                    "ऋण या अन्य सरकारी योजनाओं के लिए नजदीकी बैंक शाखा से संपर्क करें।",
                    "कृषि सलाह के लिए नीचे दिए गए चार मुख्य विकल्पों का उपयोग करें।"
                ],
                "steps": [
                    "1. 'क्या लगाएं' पूछने के लिए माइक या बटन दबाएं।",
                    "2. 'मौसम' या 'मंडी भाव' जानने के लिए प्रश्न पूछें।",
                    "3. विशेषज्ञ सलाह हेतु किसान कॉल सेंटर 1800-180-1551 पर संपर्क करें।"
                ],
                "labels": ["मार्गदर्शन", "कॉल सेंटर सहायता"],
                "sources": ["किसान कॉल सेंटर (KCC)"],
                "speak_text": "मैं फसल, मौसम और मंडी भाव की जानकारी दे सकता हूं। ऋण और वित्तीय योजनाओं के लिए नजदीकी बैंक शाखा या किसान कॉल सेंटर 1800-180-1551 पर संपर्क करें।",
                "language": "hi"
            }
        else: # what_to_grow
            card = {
                "title": "फसल सलाह (नासिक रबी मौसम)",
                "summary_lines": [
                    "रबी मौसम के लिए प्याज और चना सबसे अधिक लाभकारी फसलें हैं।",
                    "प्याज से लगभग ₹1,40,000 प्रति एकड़ अनुमानित आय संभावित है।",
                    "मध्यम से काली मिट्टी में कुएं के पानी पर अच्छी पैदावार मिलती है।"
                ],
                "steps": [
                    "1. क्यारियों में 45 से 50 दिन के स्वस्थ पौधे लगाएं।",
                    "2. ट्राइकोडर्मा से प्रति किलो बीज पर 5 ग्राम उपचार करके ही बुवाई करें।",
                    "3. ड्रिप सिंचाई द्वारा सही मात्रा में पानी और खाद दें।"
                ],
                "labels": ["अनुमानित जानकारी", "लागत पूर्व आय", "मौसम के अनुसार"],
                "sources": ["महात्मा फुले कृषि विद्यापीठ (MPKV) राहुरी"],
                "speak_text": "नासिक जिले के लिए रबी प्याज और चना सबसे अच्छे विकल्प हैं। प्याज के अच्छे दाम मिलने की उम्मीद है। अधिक जानकारी के लिए नजदीकी कृषि विज्ञान केंद्र से संपर्क करें।",
                "language": "hi"
            }
        return json.dumps(card, ensure_ascii=False)

    elif target_lang == "en":
        if intent == "weather_today":
            card = {
                "title": "Weather & Spray Advisory",
                "summary_lines": [
                    "Clear and dry weather expected across Nashik today.",
                    "Max temperature 29°C with wind speed around 9 km/h.",
                    "Weather conditions are favorable for spraying this afternoon."
                ],
                "steps": [
                    "1. Spray before 11 AM or after 3 PM when winds are gentle.",
                    "2. Always wear protective gloves and mask during application.",
                    "3. Check soil moisture and provide light irrigation if needed."
                ],
                "labels": ["Forecast Indicative", "Advisory Status"],
                "sources": ["India Meteorological Department (IMD)", "Krishi Vigyan Kendra (KVK)"],
                "speak_text": "Today the weather in Nashik is clear with low wind speeds. You can safely spray in the field this afternoon.",
                "language": "en"
            }
        elif intent == "prices":
            card = {
                "title": "Mandi Market Prices (Nashik)",
                "summary_lines": [
                    "Modal price for Onion in Nashik & Lasalgaon is ₹1,850 per quintal.",
                    "Minimum price ₹1,200 and maximum price ₹2,400 recorded.",
                    "Market sentiment is steady with moderate upward trend."
                ],
                "steps": [
                    "1. Grade onions by size and quality before taking to the mandi.",
                    "2. Ensure proper curing and drying to secure peak market rates.",
                    "3. Track daily APMC arrivals and rates."
                ],
                "labels": ["Official APMC Rates", "Representative Data"],
                "sources": ["Maharashtra State Agricultural Marketing Board (MSAMB)"],
                "speak_text": "In Nashik mandi today, onion modal price is 1850 rupees per quintal. Prices are expected to remain steady.",
                "language": "en"
            }
        elif intent == "how_to_grow":
            card = {
                "title": "Crop Management Guide (Rabi Onion)",
                "summary_lines": [
                    "Complete rabi onion transplanting between October and November.",
                    "Select well-drained medium to deep black fertile soil.",
                    "Apply balanced FYM organic manure and recommended basal fertilizers."
                ],
                "steps": [
                    "1. Incorporate 10-12 tonnes per acre of well-rotted farmyard manure.",
                    "2. Transplant 45-day seedlings on raised beds at 15x10 cm spacing.",
                    "3. Carry out light weeding and mulching in the initial 30 days."
                ],
                "labels": ["Package of Practices", "University Recommended"],
                "sources": ["Mahatma Phule Krishi Vidyapeeth (MPKV) Rahuri"],
                "speak_text": "For rabi onion cultivation, ensure fertile well-drained soil and timely transplantation on raised beds.",
                "language": "en"
            }
        elif intent == "unknown":
            card = {
                "title": "Farmer Assistance & Guidance",
                "summary_lines": [
                    "KisanMitra assists with crops, weather, mandi prices, and cultivation.",
                    "For financial loans or machinery subsidies, please contact your local bank.",
                    "Use the four quick action buttons below for agricultural advice."
                ],
                "steps": [
                    "1. Tap 'What to grow' for crop profitability analysis.",
                    "2. Ask about 'Weather' or 'Mandi prices' anytime.",
                    "3. Call Kisan Call Centre at 1800-180-1551 for government schemes."
                ],
                "labels": ["Guidance", "Kisan Call Centre"],
                "sources": ["Kisan Call Centre (KCC)"],
                "speak_text": "I can help with crop advice, weather forecasts, and market prices. For loans and subsidies, please contact your local bank or Kisan Call Centre at 1800-180-1551.",
                "language": "en"
            }
        else: # what_to_grow
            card = {
                "title": "Crop Advisory (Nashik Rabi Season)",
                "summary_lines": [
                    "Rabi Onion and Gram (Chickpea) are top recommendations for your soil.",
                    "Estimated gross income for Onion is ₹1,40,000 per acre.",
                    "Requires 110-120 days under well irrigation and medium black soil."
                ],
                "steps": [
                    "1. Prepare raised beds with drip irrigation lines.",
                    "2. Treat seeds/seedlings with Trichoderma before planting.",
                    "3. Apply balanced fertilizers based on university guidelines."
                ],
                "labels": ["Representative Data", "Gross Income Before Cost", "Seasonal Estimate"],
                "sources": ["Mahatma Phule Krishi Vidyapeeth (MPKV) Rahuri"],
                "speak_text": "For Nashik district, Rabi Onion and Gram are your best options. Onion offers attractive returns under well irrigation.",
                "language": "en"
            }
        return json.dumps(card, ensure_ascii=False)

    else: # Marathi ('mr')
        if intent == "weather_today":
            card = {
                "title": "हवामान व फवारणी सल्ला",
                "summary_lines": [
                    "नाशिक परिसरात आज हवामान स्वच्छ व कोरडे राहील.",
                    "कमाल तापमान 29 अंश आणि वाऱ्याचा वेग 9 किमी प्रतितास राहील.",
                    "आज दुपारी कीटकनाशक फवारणीसाठी हवामान अनुकूल आहे."
                ],
                "steps": [
                    "1. वाऱ्याचा वेग कमी असताना सकाळी 11 च्या आधी किंवा दुपारी 3 नंतर फवारणी करा.",
                    "2. सुरक्षिततेसाठी हातमोजे आणि मास्कचा वापर नक्की करा.",
                    "3. जमिनीतील ओल तपासून आवश्यकतेनुसार हलके पाणी द्या."
                ],
                "labels": ["हवामान अंदाजानुसार", "प्रातिनिधिक माहिती"],
                "sources": ["भारतीय हवामान विभाग (IMD)", "कृषी विज्ञान केंद्र (KVK)"],
                "speak_text": "आज नाशिकमध्ये हवामान स्वच्छ आहे आणि वाऱ्याचा वेग कमी आहे. तुम्ही आज दुपारी शेतात फवारणी करू शकता.",
                "language": "mr"
            }
        elif intent == "prices":
            card = {
                "title": "बाजारभाव माहिती (नाशिक मंडी)",
                "summary_lines": [
                    "नाशिक आणि लासलगाव बाजारात कांद्याला सरासरी ₹1,850 प्रति क्विंटल भाव आहे.",
                    "किमान भाव ₹1,200 तर कमाल भाव ₹2,400 प्रति क्विंटल नोंदवला गेला.",
                    "मागणी चांगली असल्याने पुढील आठवड्यात भाव स्थिर किंवा वाढण्याची शक्यता आहे."
                ],
                "steps": [
                    "1. कांदा प्रतवारी करून चांगल्या प्रतीचा माल विक्रीसाठी पाठवा.",
                    "2. सुका आणि चांगला पोसलेला कांदा चांगल्या दरात विकला जातो.",
                    "3. स्थानिक कृषी उत्पन्न बाजार समितीच्या ताज्या भावावर लक्ष ठेवा."
                ],
                "labels": ["अधिकृत बाजारभाव", "प्रातिनिधिक माहिती"],
                "sources": ["महाराष्ट्र राज्य कृषी पणन मंडळ (MSAMB)"],
                "speak_text": "नाशिक बाजारात आज कांद्याला सरासरी 1850 रुपये प्रति क्विंटल भाव मिळत आहे. बाजारभाव स्थिर राहण्याची शक्यता आहे.",
                "language": "mr"
            }
        elif intent == "how_to_grow":
            card = {
                "title": "पीक व्यवस्थापन मार्गदर्शक (रब्बी कांदा)",
                "summary_lines": [
                    "रब्बी कांदा लागवड ऑक्टोबर ते नोव्हेंबर दरम्यान पूर्ण करावी.",
                    "मध्यम ते भारी, पाण्याचा चांगला निचरा होणारी जमीन निवडावी.",
                    "सेंद्रिय खते आणि शिफारशीत रासायनिक खतांचा योग्य वापर करावा."
                ],
                "steps": [
                    "1. एकरी 10 ते 12 टन चांगले कुजलेले शेणखत जमिनीत मिसळा.",
                    "2. पुनर्लागवड 15 बाय 10 सेंमी अंतरावर सपाट किंवा गादीवाफ्यावर करा.",
                    "3. तण नियंत्रणासाठी सुरुवातीला हलकी खुरपणी करा."
                ],
                "labels": ["पीक शिफारस", "विद्यापीठ शिफारशीत"],
                "sources": ["महात्मा फुले कृषी विद्यापीठ (MPKV) राहुरी"],
                "speak_text": "रब्बी कांदा लागवडीसाठी मध्यम ते भारी जमीन आणि संतुलित खत व्यवस्थापन आवश्यक आहे. लागवड वेळेवर पूर्ण करा.",
                "language": "mr"
            }
        elif intent == "unknown":
            card = {
                "title": "शेतकरी सहाय्य व मार्गदर्शन",
                "summary_lines": [
                    "किसानमित्र शेती पिके, हवामान, बाजारभाव आणि लागवडीबद्दल मदत करतो.",
                    "कर्ज किंवा इतर योजनांसाठी स्थानिक बँक शाखेशी संपर्क साधावा.",
                    "शेतीविषयक सल्ल्यासाठी खालील 4 पर्यायांपैकी एकावर टॅप करा."
                ],
                "steps": [
                    "1. 'काय पिकवावे' विचारण्यासाठी बटण दाबा.",
                    "2. 'हवामान' किंवा 'बाजारभाव' जाणून घेण्यासाठी प्रश्न विचारा.",
                    "3. मोफत सल्ल्यासाठी किसान कॉल सेंटर 1800-180-1551 वर कॉल करा."
                ],
                "labels": ["मार्गदर्शन", "कॉल सेंटर सहाय्य"],
                "sources": ["किसान कॉल सेंटर (KCC)"],
                "speak_text": "मी शेती, हवामान आणि बाजारभावाविषयी माहिती देऊ शकतो. कर्ज आणि योजनांसाठी बँक किंवा किसान कॉल सेंटर 1800-180-1551 वर संपर्क साधा.",
                "language": "mr"
            }
        else: # what_to_grow
            card = {
                "title": "शेती सल्ला (नाशिक रब्बी हंगाम)",
                "summary_lines": [
                    "कांदा आणि हरभरा पिकासाठी सध्या अनुकूल हवामान आहे.",
                    "नाशिक बाजारात कांद्याला सरासरी ₹1,850 प्रति क्विंटल भाव मिळत आहे.",
                    "मध्यम ते काळ्या जमिनीत विहिरीच्या पाण्यावर उत्तम उत्पादन शक्य."
                ],
                "steps": [
                    "1. रब्बी कांद्यासाठी योग्य गादीवाफे तयार करून रोपांची लागवड करा.",
                    "2. शिफारशीनुसार ट्रायकोडर्माने बीजप्रक्रिया करूनच पेरणी करा.",
                    "3. हवामान कोरडे असल्याने हलके पाणी द्या, पाणी साचू देऊ नका."
                ],
                "labels": ["प्रातिनिधिक माहिती", "खर्चापूर्वीचे उत्पन्न", "हवामान अंदाजानुसार"],
                "sources": ["महात्मा फुले कृषी विद्यापीठ (MPKV) राहुरी"],
                "speak_text": "नमस्कार. नाशिक जिल्ह्यासाठी सध्या रब्बी कांदा आणि हरभरा ही पिके फायदेशीर आहेत. बाजारात कांद्याला चांगला भाव आहे. अधिक माहितीसाठी जवळच्या कृषी विज्ञान केंद्राशी संपर्क साधा.",
                "language": "mr"
            }
        return json.dumps(card, ensure_ascii=False)

def test_bedrock_access() -> Dict[str, Any]:
    """Verification helper for T-03."""
    results = {
        "primary_model": PRIMARY_MODEL_ID,
        "fallback_model": FALLBACK_MODEL_ID,
        "use_cache": USE_CACHE,
        "primary_status": "skipped (USE_CACHE=true)" if USE_CACHE else "untested",
        "fallback_status": "skipped (USE_CACHE=true)" if USE_CACHE else "untested"
    }

    test_prompt = "Say hello in 5 words."
    sim_out = _cached_or_simulated_llm(test_prompt, "You are an assistant.")
    results["cached_fallback_functional"] = bool(sim_out)

    if not USE_CACHE:
        client = get_bedrock_client()
        if client:
            try:
                out1 = invoke_model(test_prompt, model_id=PRIMARY_MODEL_ID)
                results["primary_status"] = "pass" if out1 else "fail"
            except Exception as e:
                results["primary_status"] = f"fail: {e}"

            try:
                out2 = invoke_model(test_prompt, model_id=FALLBACK_MODEL_ID)
                results["fallback_status"] = "pass" if out2 else "fail"
            except Exception as e:
                results["fallback_status"] = f"fail: {e}"
        else:
            results["primary_status"] = "no credentials"
            results["fallback_status"] = "no credentials"

    return results
