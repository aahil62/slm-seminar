from slmcheck import cascade, select


def row(i, hidden, public=(True,), self_=(), sig="a", diff="easy", pid="p1", cfg="m"):
    return {"cfg": cfg, "problem_id": pid, "sample_idx": i, "difficulty": diff,
            "hidden_pass": hidden, "public": list(public), "self": list(self_), "sig": sig}


def test_S0_picks_sample0():
    p = select.select([row(0, False), row(1, True)], "S0")
    assert (p.sample_idx, p.correct, p.accepted) == (0, False, None)


def test_S1_true_if_any_hidden_pass():
    assert select.select([row(0, False), row(1, True)], "S1").correct


def test_S2_first_public_passing():
    rows = [row(0, False, public=(False,)), row(1, True, public=(True,)), row(2, False)]
    p = select.select(rows, "S2")
    assert (p.sample_idx, p.accepted, p.correct) == (1, True, True)


def test_S2_falls_back_to_S0_when_none_pass():
    rows = [row(0, False, public=(False,)), row(1, False, public=(False,))]
    p = select.select(rows, "S2")
    assert (p.sample_idx, p.accepted) == (0, False)


def test_S3_max_selftests_tie_to_S2():
    rows = [row(0, False, public=(False,), self_=(True, True, False)),
            row(1, True, public=(True,), self_=(True, True, False)),
            row(2, False, public=(True,), self_=(True, False, False))]
    p = select.select(rows, "S3", tau=0.6)
    assert (p.sample_idx, p.accepted, p.correct) == (1, True, True)
    assert select.select(rows, "S3", tau=1.0).accepted is False


def test_S3_zero_selftests_falls_back_to_S2():
    rows = [row(0, False, public=(False,)), row(1, True, public=(True,))]
    assert select.select(rows, "S3") == select.select(rows, "S2")


def test_S4_largest_signature_cluster():
    rows = [row(0, False, sig="x"), row(1, True, sig="y"), row(2, True, sig="y"),
            row(3, False, sig=None)]
    p = select.select(rows, "S4")
    assert p.sample_idx == 1 and p.correct and p.accepted is False  # 2 of 4 is not a majority
    rows.append(row(4, True, sig="y"))
    assert select.select(rows, "S4").accepted is True


def test_S4_no_valid_signatures():
    p = select.select([row(0, False, sig=None), row(1, True, sig=None)], "S4")
    assert (p.sample_idx, p.accepted) == (0, False)


def test_false_pass_rate_definition():
    rows = [row(0, True, pid="a"), row(0, False, pid="b"),
            row(0, False, public=(False,), pid="c")]
    t = {(r["strategy"], r["difficulty"]): r for r in select.per_config_table(rows, "m")}
    s2 = t[("S2", "all")]
    assert s2["accept_rate"] == 2 / 3 and s2["false_pass_rate"] == 0.5
    assert s2["accuracy"] == 1 / 3 and s2["n"] == 3


def _pair(local_ok, accepted_public, llm_ok):
    slm, llm = [], []
    for k, (lo, ap, lm) in enumerate(zip(local_ok, accepted_public, llm_ok)):
        slm.append(row(0, lo, public=(ap,), pid=f"p{k}"))
        llm.append(row(0, lm, pid=f"p{k}", cfg="L"))
    return slm, llm


def test_cascade_all_accepted_equals_slm_accuracy():
    slm, llm = _pair([True, False, True], [True, True, True], [True, True, False])
    pt = [r for r in cascade.cascade_curve(slm, llm, "S2") if r["strategy"] == "S2"][0]
    assert pt["escalation_rate"] == 0 and pt["accuracy"] == 2 / 3


def test_cascade_none_accepted_equals_llm_accuracy():
    slm, llm = _pair([True, False, True], [False, False, False], [True, True, False])
    pt = [r for r in cascade.cascade_curve(slm, llm, "S2") if r["strategy"] == "S2"][0]
    assert pt["escalation_rate"] == 1 and pt["accuracy"] == 2 / 3


def test_cascade_endpoints_and_baselines():
    slm, llm = _pair([True, False, False, True], [True, False, True, True], [False, True, True, True])
    pts = cascade.cascade_curve(slm, llm, "S2")
    pt = [r for r in pts if r["strategy"] == "S2"][0]
    assert pt["escalation_rate"] == 0.25 and pt["accuracy"] == 0.75
    assert pt["oracle_acc"] >= pt["accuracy"] >= 0 and pt["oracle_acc"] >= pt["random_acc"]
    names = {r["strategy"] for r in pts}
    assert {"all-local", "all-cloud"} <= names


def test_oracle_baseline_dominates_random():
    for r in (0.0, 0.3, 0.7, 1.0):
        assert cascade.oracle_baseline([True, False, False], [False, True, True], r) >= \
            cascade.random_baseline([True, False, False], [False, True, True], r)


def test_S5_needs_examples_and_majority():
    rows = [row(0, False, public=(False,), sig="x"), row(1, True, sig="y"), row(2, True, sig="y"),
            row(3, False, sig="z")]
    p = select.select(rows, "S5")
    assert (p.sample_idx, p.correct, p.accepted) == (1, True, False)  # 2 of 4 agree: not a majority
    rows.append(row(4, True, sig="y"))
    assert select.select(rows, "S5").accepted is True


def test_S5_nothing_passes_examples():
    rows = [row(0, False, public=(False,)), row(1, True, public=(False,))]
    assert select.select(rows, "S5") == select.Pick(0, False, False, None)


def test_pick_carries_fail_kind():
    r = row(0, False)
    r["fail_kind"] = "timeout"
    assert select.select([r], "S2").fail_kind == "timeout"
