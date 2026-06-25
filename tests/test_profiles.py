"""Profile config validation and catalog completeness (spec 2.4 / 2.15)."""
from dataclasses import FrozenInstanceError

import pytest

from akribia import profiles


def test_catalog_has_all_eight_profiles():
    expected = {
        "baseline", "autism_weak_prior", "autism_overfitting", "adhd_discounting",
        "adhd_rpe_noise", "ppcs_forward_model", "comorbid",
        "audhd_emotion_dysregulation",
    }
    assert set(profiles.names()) == expected


def test_baseline_is_all_defaults():
    b = profiles.get("baseline")
    assert b.prior_precision_cap is None
    assert b.precision_flexibility == 1.0
    assert b.discount_factor == 0.95
    assert b.rpe_noise_std == 0.0
    assert b.forward_model_update_rate == 1.0
    assert b.injury_noise_std == 0.0


def test_audhd_uses_the_opposite_lever_from_weak_prior():
    # The §1.5.1 claim: autism side is high/slow precision, NOT low precision.
    audhd = profiles.get("audhd_emotion_dysregulation")
    weak = profiles.get("autism_weak_prior")
    assert audhd.prior_precision_cap is None          # NOT capped low
    assert weak.prior_precision_cap == 0.3            # capped low
    assert audhd.rpe_noise_std > 0                    # unstable gain
    assert audhd.discount_factor == 0.95              # NOT steep discounting


def test_profiles_are_frozen():
    with pytest.raises(FrozenInstanceError):
        profiles.get("baseline").discount_factor = 0.1  # type: ignore[misc]


def test_overrides_reports_only_differences():
    assert profiles.get("baseline").overrides() == {}
    assert profiles.get("adhd_discounting").overrides() == {"discount_factor": 0.6}


def test_unknown_profile_raises_with_valid_names():
    with pytest.raises(KeyError):
        profiles.get("schizophrenia")  # a roadmap profile, not built yet
