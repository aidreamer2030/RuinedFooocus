import gradio as gr
from shared import (
    state,
    performance_settings,
    resolution_settings,
    path_manager,
)

def add_api():

    # "secret" pi slideshow
    def get_last_image() -> str:
        global state
        if "last_image" in state:
            return state["last_image"]
        else:
            return "html/logo.png"

    gr.api(get_last_image, api_name="last_image")

    # llama
    from modules.llama_pipeline import run_llama
    def api_llama(system: str, user: str) -> str:
        prompt = f"system: {system}\n\n{user}"
        return run_llama(None, prompt)

    gr.api(api_llama, api_name="llama")
