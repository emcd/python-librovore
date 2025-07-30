- Merge `test_utils.py` into `fixtures.py`.
- Consistency between `query` and `term` arguments.
- Proper `<noun>_<quantifier>` names in results dictionaries. (E.g.,
  `results_max` and not `max_results`.)
- Do not return filters in results. We already know what they are.
