from core.runtime_state import RuntimeState, StepStatus


def test_runtime_state_tracks_session_context_and_steps() -> None:
    state = RuntimeState(current_user_input="hello")
    state.add_message("user", "hello")
    state.add_message("assistant", "hey")
    state.add_step("demo")

    assert state.current_user_input == "hello"
    assert len(state.conversation) == 2
    assert state.steps[0].status is StepStatus.PENDING
