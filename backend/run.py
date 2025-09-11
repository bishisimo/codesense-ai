#!/usr/bin/env python3
"""
后端启动脚本

支持通过命令行参数指定配置文件路径
"""
import argparse
import os
import sys
from pathlib import Path

import uvicorn

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="启动CodeSense AI后端服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run.py                                    # 使用默认配置
  python run.py --config /path/to/config.yaml     # 指定配置文件路径
  python run.py --config config/prod.yaml         # 使用相对路径
  python run.py --host 0.0.0.0 --port 8080       # 指定主机和端口
  python run.py --reload                          # 开发模式（热重载）
  python run.py --debug                           # 调试模式
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='配置文件路径 (支持相对路径和绝对路径)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='服务器主机地址 (默认: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8080,
        help='服务器端口 (默认: 8080)'
    )
    
    parser.add_argument(
        '--reload',
        action='store_true',
        help='启用热重载 (开发模式)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='工作进程数量 (默认: 1)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='info',
        choices=['critical', 'error', 'warning', 'info', 'debug', 'trace'],
        help='日志级别 (默认: info)'
    )
    
    args = parser.parse_args()
    
    # 处理配置文件路径
    if args.config:
        config_path = Path(args.config)
        
        # 如果是相对路径，转换为绝对路径
        if not config_path.is_absolute():
            config_path = Path.cwd() / config_path
        
        # 检查配置文件是否存在
        if not config_path.exists():
            print(f"错误: 配置文件不存在: {config_path}")
            sys.exit(1)
        
        # 设置环境变量，让配置系统使用指定的配置文件
        os.environ['CONFIG_PATH'] = str(config_path)
        print(f"使用配置文件: {config_path}")
    
    # 构建uvicorn配置
    uvicorn_config = {
        'app': 'app.main:app',
        'host': args.host,
        'port': args.port,
        'reload': args.reload,
        'log_level': args.log_level,
        'workers': args.workers if not args.reload else 1,  # 热重载模式下只能使用单进程
    }
    
    # 调试模式配置
    if args.debug:
        uvicorn_config.update({
            'reload': True,
            'log_level': 'debug',
            'reload_dirs': ['app', 'scripts'],
        })
        print("调试模式已启用")
    
    # 显示启动信息
    print("=" * 60)
    print("CodeSense AI 后端服务启动中...")
    print("=" * 60)
    print(f"主机: {uvicorn_config['host']}")
    print(f"端口: {uvicorn_config['port']}")
    print(f"热重载: {'是' if uvicorn_config['reload'] else '否'}")
    print(f"日志级别: {uvicorn_config['log_level']}")
    print(f"工作进程: {uvicorn_config['workers']}")
    if args.config:
        print(f"配置文件: {config_path}")
    print("=" * 60)
    
    # 启动服务
    try:
        uvicorn.run(**uvicorn_config)
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
