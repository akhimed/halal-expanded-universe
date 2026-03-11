from backend.app.services.explanation import build_card_explanation, build_explanation


def test_build_explanation_includes_band_and_caveat_text():
    text = build_explanation(
        name='Example Bistro',
        profile_name='balanced',
        matched_tags=['halal'],
        excluded_allergen_status=[{'allergen': 'peanut', 'present': False}],
        trust_score=0.55,
        trust_level='low',
        trust_caveats=['Low-confidence listing: use caution and verify details before visiting.'],
    )

    assert 'Low trust band (0.00-0.59)' in text
    assert 'Caveat: Low-confidence listing' in text


def test_build_card_explanation_includes_trust_band_range():
    text = build_card_explanation(
        profile_name='strict',
        matched_tags=['halal', 'zabiha'],
        trust_score=0.81,
        trust_level='high',
        trust_caveats=[],
    )

    assert 'band 80-100' in text
