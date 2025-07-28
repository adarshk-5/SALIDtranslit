import pytest

import salidtranslit

@pytest.mark.parametrize(
    "devanagari_text, bengali_text, iast_text, itrans_text",
    [
        ("विश्व", "বিশ্ব", "viśva", "vishva"),
        ("चरणध्वनि", "চরণধ্বনি", "caraṇadhvani", "charaNadhvani"),
        ("अंग", "অংগ", "aṃga", "aMga"),
        ("बारो", "বারো", "bāro", "bAro"),
        ("भक्ति", "ভক্তি", "bhakti", "bhakti"),
        ("पिता बऽले येन जानि,", "পিতা বঽলে যেন জানি,", "pitā ba'le yena jāni,", "pitA ba.ale yena jAni,"),
        (" चारि दिके मोर वसन्त हसित, यौवनकुसुम प्राणे विकशित, कुसुमेरऽपरे फेलिब चरण यौवनमाधुरीभरे।", " চারি দিকে মোর বসন্ত হসিত, যৌবনকুসুম প্রাণে বিকশিত, কুসুমেরঽপরে ফেলিব চরণ যৌবনমাধুরীভরে।", " cāri dike mora vasanta hasita, yauvanakusuma prāṇe vikaśita, kusumera'pare pheliba caraṇa yauvanamādhurībhare.", " chAri dike mora vasanta hasita, yauvanakusuma prANe vikashita, kusumera.apare pheliba charaNa yauvanamAdhurIbhare."),
        ("आत्मविड़म्बन दारुण लज्जा, निःशेषे याक से थेमे।", "আত্মবিড়ম্বন দারুণ লজ্জা, নিঃশেষে যাক সে থেমে।", "ātmavir̤ambana dāruṇa lajjā, niḥśeṣe yāka se theme.", "Atmavi.Dambana dAruNa lajjA, niHsheShe yAka se theme."),
        ("क्", "ক্", "k", "k")
    ],
)
def test_dev_trans(devanagari_text: str, bengali_text: str, iast_text: str, itrans_text: str) -> None:
    """
    Tests the transliteration of Devanagari text to Bengali, IAST, and ITRANS.
    
    Args:
        devanagari_text: The input string in Devanagari script.
        bengali_text: The expected output string in Bengali script.
        iast_text: The expected output string in IAST romanization.
        itrans_text: The expected output string in ITRANS romanization.
    """
    assert salidtranslit.transliterate("Devanagari", "Bengali", devanagari_text) == bengali_text
    assert salidtranslit.transliterate("Devanagari", "IAST", devanagari_text) == iast_text
    assert salidtranslit.transliterate("Devanagari", "ITRANS", devanagari_text) == itrans_text
    assert salidtranslit.transliterate("IAST", "Devanagari", iast_text) == devanagari_text
    assert salidtranslit.transliterate("ITRANS", "Devanagari", itrans_text) == devanagari_text

@pytest.mark.parametrize(
    "bengali_text, devanagari_text, iast_text, itrans_text",
    [
        ("বিশ্ব", "विश्व", "biśva", "bishva"),
        ("চরণধ্বনি", "चरणध्वनि", "caraṇadhvani", "charaNadhvani"),
        ("অংগ", "अंग", "aṃga", "aMga"),
        ("বারো", "बारो", "bāro", "bAro"),
        ("ভক্তি", "भक्ति", "bhakti", "bhakti"),
        ("পিতা বঽলে যেন জানি,", "पिता बऽले येन जानि,", "pitā ba'le yena jāni,", "pitA ba.ale yena jAni,"),
        (" চারি দিকে মোর বসন্ত হসিত, যৌবনকুসুম প্রাণে বিকশিত, কুসুমেরঽপরে ফেলিব চরণ যৌবনমাধুরীভরে।", " चारि दिके मोर वसन्त हसित, यौवनकुसुम प्राणे विकशित, कुसुमेरऽपरे फेलिब चरण यौवनमाधुरीभरे।", " cāri dike mora basanta hasita, yaubanakusuma prāṇe bikaśita, kusumera'pare pheliba caraṇa yaubanamādhurībhare.", " chAri dike mora basanta hasita, yaubanakusuma prANe bikashita, kusumera.apare pheliba charaNa yaubanamAdhurIbhare."),
        ("আত্মবিড়ম্বন দারুণ লজ্জা, নিঃশেষে যাক সে থেমে।", "आत्मविड़म्बन दारुण लज्जा, निःशेषे याक से थेमे।", "ātmabir̤ambana dāruṇa lajjā, niḥśeṣe yāka se theme.", "Atmabi.Dambana dAruNa lajjA, niHsheShe yAka se theme."),
        ("ক্", "क्", "k", "k")
    ],
)
def test_ben_trans(bengali_text: str, devanagari_text: str, iast_text: str, itrans_text: str) -> None:
    """
    Tests the transliteration of Bengali text to Devanagari, IAST, and ITRANS.
    
    Args:
        bengali_text: The input string in Bengali script.
        devanagari_text: The expected output string in Devanagari script.
        iast_text: The expected output string in IAST romanization.
        itrans_text: The expected output string in ITRANS romanization.
    """
    assert salidtranslit.transliterate("Bengali", "Devanagari", bengali_text) == devanagari_text
    assert salidtranslit.transliterate("Bengali", "IAST", bengali_text) == iast_text
    assert salidtranslit.transliterate("Bengali", "ITRANS", bengali_text) == itrans_text
    assert salidtranslit.transliterate("IAST", "Bengali", iast_text) == bengali_text
    assert salidtranslit.transliterate("ITRANS", "Bengali", itrans_text) == bengali_text