# safety/grey_area_topics.py
"""
Categorized culturally sensitive topics for grey-area detection (AR + EN).

Suicide / self-harm → crisis only (see CRISIS_KEYWORDS in core.config) — never listed here.
Both flags may be true when a message mixes crisis language with other sensitive topics.
"""
from __future__ import annotations

# ─── Crisis-only (documented; not used for grey matching) ─────────────────────
CRISIS_ONLY_TOPICS = {
    "suicide_self_harm": {
        "ar": "الانتحار وإيذاء النفس",
        "en": "Suicide and self-harm",
    },
}

# ─── Grey-area categories ─────────────────────────────────────────────────────
GREY_AREA_CATEGORIES: dict[str, dict] = {
    "sexual_life": {
        "ar": "الحياة الجنسية",
        "en": "Sexual life and intimacy",
        "keywords": [
            "الحياة الجنسية", "حياة جنسية", "حياتي الجنسية", "intimacy", "intimate life",
            "sexual life", "sex life", "libido", "sex drive", "bedroom", "intercourse",
            "جنس", "جنسي", "جنسية", "sex", "sexual", "sexuality",
            "masturbat", "استمن", "إستمن", "شذوذ", "fetish",
            "porn", "porno", "pornography", "إباح", "اباح", "nude", "nudes", "sexting", "onlyfans",
            "boyfriend", "girlfriend", "hookup", "one night",
        ],
    },
    "marital_problems": {
        "ar": "المشاكل الزوجية الداخلية",
        "en": "Internal marital problems",
        "keywords": [
            "مشاكل زوجية", "مشكلة زوجية", "زوجية", "marital problem", "marriage problem",
            "unhappy marriage", "bad marriage", "زوجي", "زوجتي", "husband", "wife",
            "نكد", "خلاف مع زوج", "خلاف مع زوجة", "marital conflict", "spouse",
        ],
    },
    "family_disputes": {
        "ar": "الخلافات العائلية",
        "en": "Family disputes",
        "keywords": [
            "خلافات عائلية", "خلاف عائلي", "مشاكل عائلية", "family dispute", "family conflict",
            "family fight", "family drama", "أهلي", "عائلتي", "مع أهل", "in-laws", "in laws",
        ],
    },
    "divorce": {
        "ar": "الطلاق وأسبابه",
        "en": "Divorce and separation",
        "keywords": [
            "طلاق", "طلاقي", "اطلاق", "اطلق", "طلق", "مطلق", "مطلقة", "طلقت", "طلقني", "divorce", "divorced", "separated",
            "separation", "custody", "حضانة", "نفقة",
        ],
    },
    "domestic_violence": {
        "ar": "العنف الأسري",
        "en": "Domestic violence",
        "keywords": [
            "عنف أسري", "عنف منزلي", "domestic violence", "domestic abuse", "spouse abuse",
            "beaten", "hit me", "ضربني", "ضرب", "عنف", "violence", "violent",
            "abuse", "abused", "abusive", "honor killing", "شرف",
        ],
    },
    "mental_illness": {
        "ar": "الأمراض النفسية",
        "en": "Mental illness (personal experience)",
        "keywords": [
            "مرض نفسي", "أمراض نفسية", "mental illness", "psychiatric", "psychosis",
            "schizo", "bipolar", "personality disorder", "اضطراب", "هلاوس", "وهم",
            "adhd", "ocd", "ptsd", "trauma disorder",
        ],
    },
    "addiction": {
        "ar": "الإدمان",
        "en": "Addiction",
        "keywords": [
            "إدمان", "ادمان", "addict", "addiction", "addicted",
            "كحول", "خمر", "شرب", "drunk", "alcohol", "alcoholic", "beer", "wine", "vodka",
            "مخدر", "مخدرات", "drugs", "drug", "cocaine", "weed", "cannabis", "hash", "حشيش",
            "smoking", "تدخين", "دخان", "vape", "cigarette",
            "قمار", "gambl", "رهان", "betting",
        ],
    },
    "stds": {
        "ar": "الأمراض الجنسية",
        "en": "Sexually transmitted diseases",
        "keywords": [
            "مرض جنسي", "أمراض جنسية", "std", "stds", "sti", "sexually transmitted",
            "gonorrhea", "syphilis", "herpes", "chlamydia", "hiv", "aids",
        ],
    },
    "infertility": {
        "ar": "العقم ومشاكل الإنجاب",
        "en": "Infertility and reproduction",
        "keywords": [
            "عقم", "عقيم", "infertility", "infertile", "fertility", "إنجاب", "انجاب",
            "can't get pregnant", "cannot conceive", "miscarriage", "إجهاض", "اجهاض",
            "حمل", "حامل", "pregnant", "pregnancy", "abortion",
            "ivf", "artificial insemination",
        ],
    },
    "income_wealth": {
        "ar": "الدخل الحقيقي والثروة الشخصية",
        "en": "Real income and personal wealth",
        "keywords": [
            "دخلي", "دخل حقيقي", "راتبي", "راتب", "salary", "income", "real income",
            "wealth", "ثروة", "ثروتي", "rich", "poor secretly", "financial status",
            "how much i earn", "how much money",
        ],
    },
    "debts_finance": {
        "ar": "الديون والمشاكل المالية",
        "en": "Debts and financial problems",
        "keywords": [
            "ديون", "دين", "مديون", "debt", "debts", "loan", "bankrupt", "bankruptcy",
            "financial problem", "مشاكل مالية", "مشكلة مالية", "can't pay", "broke",
            "ربا", "usury", "سرقة", "سرقت", "steal", "stole", "stolen", "fraud", "scam",
        ],
    },
    "inheritance": {
        "ar": "الميراث والخلافات عليه",
        "en": "Inheritance disputes",
        "keywords": [
            "ميراث", "ورث", "ورثة", "تركة", "inheritance", "inherit", "heir", "estate",
            "will dispute", "خلاف على الميراث", "property dispute",
        ],
    },
    "politics": {
        "ar": "التوجهات السياسية المثيرة للجدل",
        "en": "Controversial political views",
        "keywords": [
            "سياس", "political", "politics", "politician", "election", "regime",
            "انتخابات", "حكومة", "معارضة", "ثورة", "revolution", "coup",
            "controversial opinion", "political view",
        ],
    },
    "religious_criticism": {
        "ar": "انتقاد الشخصيات الدينية أو المعتقدات",
        "en": "Criticism of religious figures or beliefs",
        "keywords": [
            "انتقاد دين", "انتقاد الدين", "criticize religion", "blasphemy", "insult religion",
            "mock religion", "against islam", "against christianity", "hate religion",
            "سب الدين", "إهانة دين", "insult prophet", "mock god",
        ],
    },
    "leaving_religion": {
        "ar": "تغيير الدين أو تركه",
        "en": "Changing or leaving religion",
        "keywords": [
            "ترك الدين", "تركت الدين", "leave islam", "left islam", "apostasy", "apostate",
            "convert out", "ex-muslim", "ex muslim", "ex-christian", "renounce faith",
            "غيرت ديني", "تغيير الدين",
        ],
    },
    "personal_beliefs": {
        "ar": "المعتقدات الشخصية غير السائدة",
        "en": "Non-mainstream personal beliefs",
        "keywords": [
            "معتقد", "معتقدات", "belief", "beliefs", "atheist", "agnostic", "ملحد", "لاديني",
            "non-believer", "freethinker", "secular", "علماني",
            "سحر", "witchcraft", "magic", "طلسم", "عين", "حسد",
        ],
    },
    "orientation_identity": {
        "ar": "التوجه الجنسي والهوية الجندرية",
        "en": "Sexual orientation and gender identity",
        "keywords": [
            "مثلية", "مثلي", "مثليون", "lgbt", "lgbtq", "lgbtqia", "همجنس", "متحول",
            "queer", "gay", "lesbian", "homosexual", "homosexuality", "bisexual",
            "transgender", "nonbinary", "non-binary", "gender identity", "gender dysphoria",
            "asexual", "pansexual", "هوية جندرية", "توجه جنسي",
        ],
    },
    "harassment_assault": {
        "ar": "التجارب الشخصية مع التحرش أو الاعتداء",
        "en": "Harassment or assault experiences",
        "keywords": [
            "تحرش", "تحرشت", "harass", "harassed", "harassment", "molest", "molested",
            "اغتصاب", "اغتص", "اغتصب", "rape", "raped", "rapist", "assault", "assaulted",
            "sexual assault", "abused sexually", "اعتداء", "اعتدى",
            "bullying", "تنمر", "blackmail", "ابتزاز", "extort", "ابتز",
        ],
    },
    "criminal_legal": {
        "ar": "السجل الجنائي أو المشكلات القانونية",
        "en": "Criminal record or legal trouble",
        "keywords": [
            "سجل جنائي", "criminal record", "criminal", "felony", "misdemeanor",
            "prison", "jail", "سجن", "محكمة", "court", "lawsuit", "legal trouble",
            "arrest", "arrested", "charged with", "convicted", "probation", "parole",
            "حادث", "accident", "crashed",
        ],
    },
    "family_secrets": {
        "ar": "الأسرار العائلية القديمة",
        "en": "Old family secrets",
        "keywords": [
            "سر عائلي", "أسرار عائلية", "family secret", "hidden from family",
            "secret from parents", "ما بعرف أهلي", "don't tell my family", " ashamed to tell family",
        ],
    },
    "infidelity": {
        "ar": "الخيانة الزوجية",
        "en": "Marital infidelity",
        "keywords": [
            "خيانة", "خنت", "خيانة زوجية", "cheating", "cheated", "affair", "mistress",
            "علاقة سرية", "علاقة محرمة", "حب حرام", "secret relationship",
            "زنا", "زنيت", "زنى", "زاني", "fornication", "adultery", "adulter",
            "عهر", "prostitut", "دعارة",
        ],
    },
    "children_problems": {
        "ar": "مشاكل الأبناء السلوكية أو التعليمية",
        "en": "Children's behavioral or educational problems",
        "keywords": [
            "مشاكل أبناء", "مشكلة ابني", "مشكلة ابنتي", "child behavior", "son problem",
            "daughter problem", "teen trouble", "adolescent", "مراهق", "طفل مشكل",
            "school problem", "مشاكل مدرسة", "تربية", "parenting shame",
        ],
    },
    "tribal_clan": {
        "ar": "الخلافات القبلية أو العشائرية",
        "en": "Tribal or clan disputes",
        "keywords": [
            "قبلي", "قبيلة", "عشيرة", "عشائري", "tribal", "clan", "clan dispute",
            "tribe", "blood feud", "ثأر", "نسب", "lineage shame",
        ],
    },
    "failure_shame": {
        "ar": "الفشل الدراسي أو المهني",
        "en": "Academic or professional failure",
        "keywords": [
            "فشل", "فاشل", "failed", "failure", "رسب", "راسب", "dropout", "dropped out",
            "fired", "terminated", "lost my job", "unemployed", "بطالة", "فصلوني",
            "professional failure", "career failure", "academic failure",
        ],
    },
    "private_physical_health": {
        "ar": "تفاصيل الصحة الجسدية الخاصة",
        "en": "Private physical health details",
        "keywords": [
            "تفاصيل صحية", "مرض خاص", "chronic illness", "medical condition",
            "diagnosis", "symptoms private", "embarrassing illness", "disability hidden",
            "impotence", "erectile", "incontinence",
        ],
    },
    "real_age": {
        "ar": "العمر الحقيقي",
        "en": "Real age (sensitive context)",
        "keywords": [
            "عمري الحقيقي", "سني الحقيقي", "my real age", "lying about my age",
            "أكبر مما", "أصغر مما", "fake age", "age shame",
        ],
    },
    "cosmetic_surgery": {
        "ar": "عمليات التجميل والإجراءات الطبية الخاصة",
        "en": "Cosmetic surgery and private procedures",
        "keywords": [
            "تجميل", "عملية تجميل", "plastic surgery", "cosmetic surgery", "nose job",
            "liposuction", "botox", "silicone", "عملية سرية", "surgery secret",
        ],
    },
    "honor_reputation": {
        "ar": "الخلافات المتعلقة بالشرف والسمعة",
        "en": "Honor and reputation",
        "keywords": [
            "شرف", "سمعة", "سمعتي", "reputation", "honor", "عار", "عيب", "فضيحة", "stigma",
            "shame", "ashamed", "حرام", "haram", "ذنب", "ذنوب", "guilt", "guilty",
            "ندم", "ندمان", "sin", "sinful", "repent", "توبة", "تائب",
            "social standing", "المكانة الاجتماعية", "سمعة شخصية", "سمعة العائلة",
            "family honor", "honour",
        ],
    },
    "assets_property": {
        "ar": "تفاصيل الممتلكات والأصول المالية",
        "en": "Assets and property",
        "keywords": [
            "ممتلكات", "أصول", "assets", "property", "real estate", "عقار", "عقارات",
            "secret savings", "hidden money", "offshore", "undeclared wealth",
        ],
    },
    "family_mental_health": {
        "ar": "المشاكل النفسية داخل الأسرة",
        "en": "Family mental health problems",
        "keywords": [
            "نفسية الأسرة", "family mental", "parent depression", "mother sick mentally",
            "father mental", "أم مريضة نفس", "أبي مريض نفس", "sibling mental illness",
        ],
    },
    "pre_marital": {
        "ar": "العلاقات السابقة قبل الزواج",
        "en": "Pre-marital relationships",
        "keywords": [
            "قبل الزواج", "pre-marital", "premarital", "before marriage", "ex before marriage",
            "علاقات سابقة", "past relationship", "former lover", "حبيب سابق", "خطيب سابق",
            "engagement", "خطوبة", "broken engagement", "زواج", "marriage",
        ],
    },
    "socially_embarrassing": {
        "ar": "تجارب شخصية محرجة اجتماعيًا",
        "en": "Socially embarrassing personal experiences",
        "keywords": [
            "محرج", "محرجة", "embarrassing", "embarrassed", "humiliating", "humiliated",
            "socially awkward shame", "ضحك عل", "رماني", "شب و", "كذب", "كذبت", "lied", "lying",
            "incest", "قريب", "forced marriage", "زواج قسري",
        ],
    },
    "relationships_general": {
        "ar": "علاقات وحميمية (عام)",
        "en": "Relationships and intimacy (general)",
        "keywords": [
            "حبيب", "حبيبة", "حبيبي", "علاقة", "relationship", "breakup", "انفصل",
            "engagement", "خطوبة", "fiancé", "fiancée",
        ],
    },
}

# Flat keyword list for fast substring matching (longer phrases first helps specificity)
GREY_AREA_KEYWORDS: list[str] = sorted(
    {kw for cat in GREY_AREA_CATEGORIES.values() for kw in cat["keywords"]},
    key=len,
    reverse=True,
)

CATEGORY_LABELS: dict[str, str] = {
    cat_id: f"{meta['en']} / {meta['ar']}" for cat_id, meta in GREY_AREA_CATEGORIES.items()
}


def match_grey_categories(text: str) -> list[str]:
    """Return category ids whose keywords appear in text (case-insensitive)."""
    if not text or not text.strip():
        return []
    lowered = text.lower()
    matched: list[str] = []
    for cat_id, meta in GREY_AREA_CATEGORIES.items():
        for kw in meta["keywords"]:
            if kw.lower() in lowered:
                matched.append(cat_id)
                break
    return matched
