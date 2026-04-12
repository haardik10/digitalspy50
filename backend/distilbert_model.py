import os
import re
import torch
import torch.nn as nn
from transformers import DistilBertTokenizerFast, DistilBertModel

# ======================================================
# 1. Paths and device
# ======================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "hybrid_distilbert_cased_ihopefinal.pt")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"✅ DistilBERT using device: {DEVICE}")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")

# ======================================================
# 2. Tokenizer
# ======================================================
tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-cased")

# ======================================================
# 3. Hybrid Model Definition
# ======================================================
class DistilBertHybrid(nn.Module):
    def __init__(self, num_numeric_features=12, dropout_rate=0.3):
        super().__init__()
        self.bert = DistilBertModel.from_pretrained("distilbert-base-cased")
        self.numeric_layer = nn.Sequential(
            nn.Linear(num_numeric_features, 16),
            nn.ReLU(),
            nn.Dropout(dropout_rate)
        )
        self.classifier = nn.Sequential(
            nn.Linear(self.bert.config.hidden_size + 16, 64),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(64, 2)
        )

    def forward(self, input_ids, attention_mask, numeric_feats=None):
        bert_output = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = bert_output.last_hidden_state[:, 0]

        if numeric_feats is not None:
            numeric_output = self.numeric_layer(numeric_feats)
        else:
            numeric_output = torch.zeros(
                pooled_output.size(0), 16, device=pooled_output.device
            )

        combined = torch.cat((pooled_output, numeric_output), dim=1)
        logits = self.classifier(combined)
        return {"logits": logits}

# ======================================================
# 4. Load model
# ======================================================
model = DistilBertHybrid(num_numeric_features=12)

state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)

if missing_keys:
    print("⚠️ Missing keys:", missing_keys)
if unexpected_keys:
    print("⚠️ Unexpected keys:", unexpected_keys)

model.to(DEVICE)
model.eval()

# ======================================================
# 5. Cleaning pipeline
# ======================================================
def distilbert_cased_clean(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s.,!?&]", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def clean_publishers_and_promos(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"http\S+|www\.\S+|pic\.twitter\.com\S+|@\w+", "", text)
    text = re.sub(
        r"(?i)\b("
        r"read\s*more|continue\s*reading|subscribe|become\s*a\s*member|support\s+21wire|join\s*now|donate|"
        r"follow\s*us|watch\s*live|visit\s*our\s*site|learn\s*more|for\s*full\s*story|read\s*the\s*full\s*story|"
        r"support\s*our\s*work|subscribe\s*and\s*become|register\s*here"
        r")\b.*",
        "",
        text
    )
    agency_pattern = (
        r"(?i)\b("
        r"Reuters|Associated\s*Press|AP|AFP|BBC|CNN|MSNBC|NBC|ABC|CBS|"
        r"Fox\s*News|FOX\d{2,}|Fox\d{2,}|NYT|New\s+York\s+Times|"
        r"The\s+Times|Bloomberg|WSJ|Wall\s+Street\s+Journal|Guardian|"
        r"Politico|Newsmax|The\s+Hill|USA\s*Today|Time\s*Magazine|"
        r"Al\s*Jazeera|Sky\s*News|HuffPost|Daily\s*Mail|BuzzFeed|"
        r"NPR|CNBC|Breaking911|Infowars|Wsvn|Wftv|Cbsnews|Fox35|"
        r"TeaPainUSA|RobbinSimmons7|LWOSmwilson1113|RunBeast|NFB|"
        r"PiinkyPants1|SusannG|Mugrage|ShannonMugrage|"
        r"21WIRE|21st\s*Century\s*Wire|CONSORTIUM\s*NEWS|"
        r"POLITICO\s*Morning\s*Consult|WIRED\s*FILES|DAILY\s*SHOOTER|"
        r"CNNREAD|BBCNEWS|NBCNEWS|CBSNEWS"
        r")\b"
    )
    text = re.sub(agency_pattern, "", text)
    text = re.sub(r"(?i)\b(NEWS\s+AT\s+[A-Z0-9\s]+|FILESREAD\s+MORE|WIRE\s+\w+FILES)\b", "", text)
    text = re.sub(r"\b\d{3,4}\s*(AM|PM|EDT|EST|GMT|UTC)\b", "", text)
    text = re.sub(r"bit\.ly\S+|tinyurl\S+|t\.co\S+", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def remove_agency_variants(text):
    if not isinstance(text, str):
        return ""
    pattern = (
        r"(?i)([a-z0-9_-]*)(?:"
        r"reuters?|bbc|cnn|nbc|fox|ap|associated\s*press|bloomberg|guardian|politico|"
        r"newsmax|hill|npr|buzzfeed|al\s*jazeera|huffpost|nytimes?|washington\s*post|"
        r"usa\s*today|msnbc|abc|cbs|pbs|axios|forbes|insider|telegraph|economist|vox|"
        r"slate|daily\s*mail|time\s*magazine|new\s*yorker|wall\s*street\s*journal|wsj|"
        r"21wire|infowars|breitbart|oann|the\s*sun|mirror|dailymirror|independent|"
        r"sky\s*news|evening\s*standard|express|metro|newsweek|cnbc|cnet|espn|"
        r"dw|rtl|deccan\s*chronicle|times\s*of\s*india|hindustan\s*times|"
        r"indian\s*express|ndtv|ani|republic\s*tv|zee\s*news|abp\s*news"
        r")([a-z0-9_-]*)"
    )
    cleaned = re.sub(pattern, " ", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


def remove_prefix_suffix_jargon(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"(?i)\b(by|reporting\s+by|editing\s+by|filed\s+by|with\s+reporting\s+by)\b[^.]{0,120}\.", " ", text)
    text = re.sub(r"^[A-Z\s]+\(Reuters\)\s*[-–]\s*", "", text)
    text = re.sub(r"\(This\s+story[^)]*\)", "", text)
    text = re.sub(r"(?i)©\s*\d{4}[^.]*all rights reserved.*$", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


REMOVE_PATTERN = r"(?i)\b(source:|more on this|read full story|copyright|\(ap\)|\(afp\))[^.]*\.?"


def final_normalize_series(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"(https?:\/\/|www\.|\.com|\.co\.uk|\.in)\S*", "", text)
    text = re.sub(REMOVE_PATTERN, "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def full_clean_pipeline(text):
    text = distilbert_cased_clean(text)
    text = clean_publishers_and_promos(text)
    text = remove_agency_variants(text)
    text = remove_prefix_suffix_jargon(text)
    text = final_normalize_series(text)
    return text

# ======================================================
# 6. Prediction
# ======================================================
def predict_news(text):
    if not isinstance(text, str) or not text.strip():
        return {
            "prediction": "Unknown",
            "confidence": 0.0,
            "color": "gray"
        }

    text = full_clean_pipeline(text)

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=384
    )
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

    with torch.inference_mode():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs["logits"], dim=1)

        confidence, pred_class = torch.max(probs, dim=1)

    # 🔥 Map class → prediction
    if pred_class.item() == 1:
        prediction = "Real"
        color = "green"
    else:
        prediction = "Fake"
        color = "red"

    return {
        "prediction": prediction,
        "confidence": float(confidence.item()),
        "color": color
    }