from utils.config_handler import prompts_conf
from utils.path_tool import get_abs_path


def _load_prompt(config_key: str) -> str:
    prompt_path = get_abs_path(prompts_conf[config_key])
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def load_system_prompts() -> str:
    return _load_prompt("main_prompt_path")


def load_rag_prompts() -> str:
    return _load_prompt("rag_summarize_prompt_path")


def load_report_prompts() -> str:
    return _load_prompt("report_prompt_path")
