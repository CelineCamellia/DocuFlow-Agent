#工具调用监控、模型调用前日志、动态切换提示词

from typing import Callable  # Callable 表示“可调用对象”，一般就是函数
from utils.prompt_loader import load_system_prompts, load_report_prompts  # 加载普通系统提示词 / 报告生成提示词
from langchain.agents import AgentState  # AgentState：整个 Agent当前的状态记录，比如 messages
from langchain.agents.middleware import wrap_tool_call, before_model, dynamic_prompt, ModelRequest
# wrap_tool_call：工具调用前后插入逻辑
# before_model：模型调用前插入逻辑
# dynamic_prompt：动态切换提示词
# ModelRequest：模型请求对象，里面有 runtime 等信息
from langchain.tools.tool_node import ToolCallRequest  # 工具调用请求对象，里面有工具名、参数等信息
from langchain_core.messages import ToolMessage  # 工具返回给 Agent 的消息类型
from langgraph.runtime import Runtime  # 运行时上下文信息，可以存放跨步骤共享的信息
from langgraph.types import Command  # LangGraph 的控制命令类型
from utils.logger_handler import logger  # 日志器，用于记录中间件执行过程


# 中间件 1：工具调用监控
# 作用：在工具真正执行前后记录日志，并在调用 fill_context_for_report 时打上 report 标记
@wrap_tool_call
def monitor_tool(
        request: ToolCallRequest,  # 入参：当前工具调用请求，里面包含工具名、参数、runtime 等信息
        handler: Callable[[ToolCallRequest], ToolMessage | Command],  # 真正执行工具的函数
) -> ToolMessage | Command:  # 返回工具执行结果，可能是 ToolMessage 或 Command

    logger.info(f"[tool monitor]执行工具：{request.tool_call['name']}")  # 记录当前要执行的工具名
    logger.info(f"[tool monitor]传入参数：{request.tool_call['args']}")  # 记录当前工具的入参

    try:
        result = handler(request)  # 真正执行工具；monitor_tool只是包了一层监控逻辑
        logger.info(f"[tool monitor]工具{request.tool_call['name']}调用成功")  # 工具执行成功后记录日志

        if request.tool_call['name'] == "fill_context_for_report":  # 如果调用的是“报告上下文填充工具”
            request.runtime.context["report"] = True  # 在运行时上下文中打标记，表示进入报告生成场景（原来默认为false)

        return result  # 返回工具执行结果，交给 Agent 后续流程继续处理

    except Exception as e:
        logger.error(f"工具{request.tool_call['name']}调用失败，原因：{str(e)}")  # 工具执行失败时记录错误日志
        raise e  #抛出异常，传到上层，若上层未捕获，则程序终止


# 中间件 2：模型调用前日志
# 作用：在每次调用大模型前，"记录"当前消息数量和最后一条消息内容，方便调试 Agent 流程
@before_model
def log_before_model(
        state: AgentState,  # 整个 Agent 当前状态，里面通常有 messages
        runtime: Runtime,   # 运行时上下文信息
):
    logger.info(f"[log_before_model]即将调用模型，带有{len(state['messages'])}条消息。")  # 记录当前上下文消息数量

    logger.debug(
        f"[log_before_model]{type(state['messages'][-1]).__name__} | {state['messages'][-1].content.strip()}"
    )  # 记录最后一条消息（-1的含义）的类型和内容，debug 级别用于调试

    return None  # 这里只是记录日志，不修改 Agent 状态，无需返回值(因为函数输出return值会代替输入的位置）


# 中间件 3：动态提示词切换
# 作用：每次生成提示词前，根据 runtime.context 中的 report 标记，决定使用普通提示词还是报告提示词
@dynamic_prompt
def report_prompt_switch(request: ModelRequest):  # request 是模型请求对象，里面包含 runtime 等信息
    is_report = request.runtime.context.get("report", False)  # 从上下文中读取 report 标记（通过get函数得到report里面的key)，没有则默认为 False

    if is_report:  # 如果 report=True，说明当前进入报告生成场景
        return load_report_prompts()  # 返回报告生成提示词（report_prompt.txt）（prompt_loader.py里面告诉程序了提示词文件在哪）

    return load_system_prompts()  # 默认返回普通系统提示词（main_prompt.txt ）（prompt_loader.py里面告诉程序了提示词文件在哪）