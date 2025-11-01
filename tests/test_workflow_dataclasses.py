from automation.workflow import Step, Workflow, save_workflow, load_workflow


def test_workflow_serialization(tmp_path):
    step = Step(id="start", name="Start", next=["end"])
    workflow = Workflow(steps={"start": step})
    path = tmp_path / "workflow.yaml"
    save_workflow(workflow, path)
    loaded = load_workflow(path)
    assert loaded.steps["start"].name == "Start"
    assert loaded.steps["start"].next == ["end"]
