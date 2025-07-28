# SALIDtranslit

SALIDtranslit is a Python package that aims to provide transliteration for Indian languages. For this project, we focus on transliterating Bengali since it’s a low-resource language, with a particular emphasis on the “ba/va” problem. The “ba/va” problem comes from the Bengali character ব making either a “ba” or a “va” sound depending on context, but current transliteration libraries like Aksharamukha map ব to “ba” in all contexts, leading to inaccurate transliterations. To solve this problem, we develop high-quality datasets derived from Bengali literature and use string processing and machine learning methods to transliterate Bengali text, achieving over 95% accuracy while running more efficiently than current transliteration methods.

## Next Steps:
- [ ] Verify accuracy of training/validation/evaluation datasets and clean/refine as needed
- [ ] Implement system for catching common ambiguous words without using transliteration model
- [ ] Implement post-processing system for transliteration model to reduce errors arising from model output
