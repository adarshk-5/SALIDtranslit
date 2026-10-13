# Data Card: SALIDtranslit release sample

*Last updated: October 2026. Anonymous release for double-blind review.*

## Summary

A stratified sample of whole sentences from a manually verified Bengali–Devanagari parallel corpus of 19th- and 20th-century literary works, labeled for the Bengali *ba/va* decision (ব → ब or व). The full corpus has 178,945 sentences by eight authors and is **not** redistributed. The release contains 2,334 sentences and 6,723 labeled occurrences of ব, drawn only from works whose redistribution is permitted.

| | |
|---|---|
| Language and scripts | Bengali (Bangla) text with Devanagari transliterations |
| Genres | novels, poetry, plays, short stories, songs |
| Period | 19th and 20th century |
| Release size | 2,334 sentences; 6,723 labeled occurrences |
| Files | `release_sentences.csv`, `release_occurrences.csv`, `sampling_report.csv`, `sampling_report_composition.csv`, `manifest.json` (columns are described in the repository README) |

## Intended use

- Evaluating and comparing Bengali→Devanagari transliteration, in particular the *ba/va* decision, and reproducing the sample-level results in the paper.
- **Not intended for** estimating how often *ba/va* occurs in Bengali text (the sample is deliberately stratified, 30.24% *va* against 6.3% in the full corpus), for conclusions about modern or informal Bengali, or as a substitute for the original works.

## Source texts and rights

Rights information for each author in the corpus. Status is for India as of 2026, the applicable term is the author's lifetime plus 60 years.

| Author (as in the release) | Died | Status in India (2026) | Corpus sentences | In release | Sentences in release |
|---|---:|---|---:|---|---:|
| Rabindranath Tagore | 1941 | Public domain | 80,086 | Yes | 890 |
| Saratchandra Chattopadhyay | 1938 | Public domain | 53,699 | Yes | 615 |
| Kazi Nazrul Islam | 1976 | **Not yet public domain; permission required** | 21,641 | **No** | 0 |
| Bankim Chandra Chatterjee | 1894 | Public domain | 20,866 | Yes | 548 |
| Sukumar Ray | 1923 | Public domain | 1,592 | Yes | 134 |
| Upendrakishore Ray Chowdhury | 1915 | Public domain | 892 | Yes | 62 |
| Sukanta Bhattacharya | 1947 | Public domain | 138 | Yes | 62 |
| Michael Madhusudan Dutta | 1873 | Public domain | 31 | Yes | 23 |


Notes on rights:

- The works of **Kazi Nazrul Islam** are excluded from the release in full. Under the lifetime-plus-60 term they are expected to enter the public domain in India at the start of 2037.
- The status above concerns the authors' works. The specific digital editions and transcriptions come from the source archives below, which may have their own terms of use.
- Public-domain status was assessed for India only. Other jurisdictions may differ: for works published after 1931, they may not be public domain in the United States of America, which may apply to some sentences by Tagore, Chattopadhyay, and Bhattacharya.

## Provenance

The works of Tagore, Chattopadhyay, Nazrul Islam and Chatterjee were obtained from the corresponding archives of the Society for Natural Language Technology Research; the works of the other authors were obtained from the BengaliOnline archive (full references are in the paper). Most of the 178,945 sentences (174,934) were selected because they contain ব; the remaining 4,011 come from shorter works and are not filtered on ব. 

We include the URLs for the archives here:
- [BengaliOnline Archive](https://www.isid.ac.in/~deepayan/bengalionline.net/static.html)
- [Rabindra Rachanabali](https://rabindra-rachanabali.nltr.org/node/1)
- [Sarat Rachanabali](https://sarat-rachanabali.nltr.org/)
- [Nazrul Rachanabali](https://nazrul-rachanabali.nltr.org/)
- [Bankim Rachanabali](https://bankim-rachanabali.nltr.org/)

## Annotation

Each Bengali sentence received a Devanagari transliteration from an earlier version of SALIDtranslit, which one annotator then corrected. The annotator is a native Bengali speaker with experience in linguistics research and verified every transliteration. The references follow one pronunciation-based convention: ব is written व only when it directly follows a virama after one of 16 consonants, and ब everywhere else. There is a single annotator, so no inter-annotator agreement is available. The earlier draft is not released.

## Sampling

A category is the consonant immediately before the sequence virama + ব together with the reference label (20 attested categories, 16 with *va* and four with *ba*), plus a control category of ব outside conjuncts. For each category, up to 200 sentences were drawn without replacement from sentences that are permitted for redistribution, are not exact duplicates, and whose ব count matches the reference's ब/व count. Categories are processed from rarest to most common, and within a category sentences are drawn evenly across author and sentence-length groups. Each sentence is released once with every ব labeled. The parameters, random seed and input checksum are in `manifest.json`; per-category counts in the full corpus and in the sample, with author and length composition, are in `sampling_report.csv` and `sampling_report_composition.csv`.

## Licensing and takedown

- **Annotations** (Devanagari references, labels and sampling metadata): CC BY-SA 4.0.
- **Bengali text:** the released works are in the public domain in India; we assert no additional rights over the text.
- **Code:** MIT License.
- If you hold rights in any released text and believe it should not be included, contact [Author Name] (<author.email@institution.edu>) and the affected sentences will be removed from the release. Contact details are omitted for double-blind review. Real contact info will be restored upon acceptance.

## Known limitations

- The sample is stratified, not random; category proportions are not natural frequencies.
- Agreement with the references is not an independent measure of linguistic correctness, because the references began as output of an earlier version of the tool and were corrected by one annotator.
- The corpus is 19th- and 20th-century literary text from a small set of authors; modern or informal Bengali may behave differently.
- One author (Kazi Nazrul Islam) is excluded for rights reasons, which removes a major poetic voice from the release.