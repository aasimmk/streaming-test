from typing_extensions import override
# noinspection PyProtectedMember
from openai import OpenAI, AssistantEventHandler
from backend._config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


class EventHandler(AssistantEventHandler):
    """
    Even handler for OpenAI Assistant API.
    """
    @override
    def on_event(self, event):
        """
        Retrieve events that are denoted with 'requires_action'
        since these will have our tool_calls
        """
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id
            self.handle_requires_action(event.data, run_id)

    def handle_requires_action(self, data, run_id):
        """
        Submit all tool_outputs at the concurrently
        """
        tool_outputs = []

        for tool in data.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == "get_current_temperature":
                tool_outputs.append({"tool_call_id": tool.id, "output": "57"})
            elif tool.function.name == "get_rain_probability":
                tool_outputs.append({"tool_call_id": tool.id, "output": "0.06"})

        self.submit_tool_outputs(tool_outputs, run_id)

    # noinspection PyUnusedLocal
    def submit_tool_outputs(self, tool_outputs, run_id):
        """
        Stream response from OpenAI API
        """
        with client.beta.threads.runs.submit_tool_outputs_stream(
                thread_id=self.current_run.thread_id,
                run_id=self.current_run.id,
                tool_outputs=tool_outputs,
                event_handler=EventHandler(),
        ) as stream:
            for text in stream.text_deltas:
                print(text, end="", flush=True)
