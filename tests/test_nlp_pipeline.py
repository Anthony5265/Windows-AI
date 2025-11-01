from domains.natural_language_processing import (
    input_processor,
    task_planner,
    executor,
    result_aggregator,
)


def test_pipeline_local():
    text = "Hello, world!"
    tokens = input_processor(text)
    # punctuation should be removed and words lowercased
    assert tokens == ["hello", "world"]

    plan = task_planner(tokens)
    assert plan["plan"][0]["type"] == "local"

    results = executor(plan)
    aggregated = result_aggregator(results)

    assert aggregated["results"] == ["LOCAL:hello world"]


def test_pipeline_remote():
    text = "This is a considerably longer sentence designed for remote processing."
    tokens = input_processor(text)
    assert len(tokens) > 5

    plan = task_planner(tokens)
    assert plan["plan"][0]["type"] == "remote"

    results = executor(plan)
    aggregated = result_aggregator(results)

    assert aggregated["results"] == ["REMOTE:" + " ".join(tokens)]
