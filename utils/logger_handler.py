import logging
from utils.path_tool import get_abs_path  # 将相对路径转换为项目内的绝对路径
import os
from datetime import datetime

# 日志保存的根目录，以后都会在这个文件夹里面写日志了
LOG_ROOT = get_abs_path("logs")

# 确保日志的目录存在，如果不存在就创建，存在的话啥事没有
os.makedirs(LOG_ROOT, exist_ok=True)

# 日志的格式配置  时间 - 日志器名称 - 日志级别 - 文件名:行号 - 日志内容 （debug调试信息＜info运行信息＜warning警告信息＜error错误信息）
DEFAULT_LOG_FORMAT = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)


def get_logger(
        name: str = "agent",
        console_level: int = logging.INFO,   #配置默认级别，控制台默认只显示INFO及以上级别日志
        file_level: int = logging.DEBUG,     #配置文件级别，日志文件里默认记录DEBUG及以上级别日志
        log_file = None,
) -> logging.Logger:     #创建并配置一个 logger 日志对象
    logger = logging.getLogger(name)   #根据 name 创建/获取一个日志器
    logger.setLevel(logging.DEBUG)     #设置 logger 的总日志级别

    # 避免重复添加Handler，保证logger不管导入多少次只有一次Handler
    if logger.handlers:
        return logger

    # 控制台Handler（可以在控制台显示日志）
    console_handler = logging.StreamHandler() #控制台处理器
    console_handler.setLevel(console_level)   #处理器的级别
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)  #输出日志的格式

    logger.addHandler(console_handler)

    # 文件Handler（不仅在控制台，还可以在文件里面显示）
    #没有手动指定日志文件路径，就自动生成一个默认日志文件路径
    if not log_file:        # 日志文件的存放路径
        log_file = os.path.join(LOG_ROOT, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")

    file_handler = logging.FileHandler(log_file, encoding='utf-8')  # 创建文件日志处理器，负责把日志写入文件
    file_handler.setLevel(file_level)    #设置写入文件的日志级别
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)    #设置文件日志输出格式

    logger.addHandler(file_handler)        #将文件处理器添加到 logger 中

    return logger


# 快捷获取日志器
logger = get_logger()


if __name__ == '__main__':
    logger.info("信息日志")
    logger.error("错误日志")
    logger.warning("警告日志")
    logger.debug("调试日志")