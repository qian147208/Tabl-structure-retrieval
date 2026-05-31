#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
网页版数据库数据导出平台 - Flask后端应用
"""

import os
import secrets
import json
import zipfile
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, session
from urllib.parse import unquote, quote
from flask_session import Session
from db.factory import DatabaseConnectionFactory
from db.excel_exporter import ExcelExporter
from db.csv_exporter import CSVExporter
from db.logger import get_logger

logger = get_logger()

# 创建Flask应用
app = Flask(__name__)

# 配置会话 - SECRET_KEY从环境变量读取，如果没有则生成随机值
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = 'flask_session'
app.config['SESSION_PERMANENT'] = False

# 初始化会话
Session(app)

# 确保输出目录存在
OUTPUT_DIR = 'web_output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 数据库连接会话存储（不保存密码）
connections = {}

# 连接超时时间（秒）
CONNECTION_TIMEOUT = 1800  # 30分钟


def cleanup_expired_connections(current_session=None):
    """清理过期的数据库连接
    
    Args:
        current_session: Flask session对象（可选），传入时同时清理过期session
    """
    current_time = datetime.now().timestamp()
    expired_ids = []
    
    for conn_id, conn in connections.items():
        try:
            if hasattr(conn, 'last_used'):
                if current_time - conn.last_used > CONNECTION_TIMEOUT:
                    expired_ids.append(conn_id)
            elif hasattr(conn, 'connection') and conn.connection:
                # 尝试测试连接是否有效
                try:
                    conn.connection.rollback()
                    # 如果成功回滚成功，更新last_used
                    conn.last_used = current_time
                except Exception:
                    # 连接无效，标记过期
                    expired_ids.append(conn_id)
            else:
                # 无连接对象，标记过期
                expired_ids.append(conn_id)
        except Exception:
            expired_ids.append(conn_id)
    
    for conn_id in expired_ids:
        try:
            if conn_id in connections:
                connections[conn_id].disconnect()
        except Exception:
            pass
        finally:
            if conn_id in connections:
                del connections[conn_id]
        
        # 如果传入了session对象，清理对应的session
        if current_session:
            if 'connection_id' in current_session and current_session['connection_id'] == conn_id:
                current_session.pop('connection_id', None)
                current_session.pop('db_info', None)
    
    if expired_ids:
        logger.info(f"已清理 {len(expired_ids)} 个过期连接")


@app.route('/')
def index():
    """首页 - 数据库连接登录页面"""
    return render_template('index.html')


@app.route('/tables')
def tables():
    """表列表页面"""
    # 检查是否已连接
    if 'connection_id' not in session:
        return render_template('index.html', error="请先连接数据库")
    
    return render_template('tables.html')


@app.route('/api/connect', methods=['POST'])
def api_connect():
    """连接数据库并获取表列表"""
    try:
        # 清理过期连接
        cleanup_expired_connections(session)
        
        data = request.get_json()
        
        # 处理重新连接
        if data.get('reconnect'):
            if 'connection_id' in session and session['connection_id'] in connections:
                connection_id = session['connection_id']
                conn = connections[connection_id]
                # 更新连接使用时间
                conn.last_used = datetime.now().timestamp()
                tables = conn.get_tables()
                return jsonify({
                    'success': True,
                    'message': '已恢复连接',
                    'tables': tables,
                    'count': len(tables)
                })
            else:
                return jsonify({'success': False, 'message': '未找到连接会话'}), 401
        
        # 验证必填字段
        required_fields = ['db_type', 'host', 'port', 'user', 'password', 'database']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'缺少必填字段: {field}'}), 400
        
        # 验证并转换端口号
        try:
            port = int(data['port'])
            if port < 1 or port > 65535:
                return jsonify({'success': False, 'message': '端口号必须在1-65535之间'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': '端口号必须是有效数字'}), 400
        
        # 创建数据库连接
        conn = DatabaseConnectionFactory.create_connection(
            data['db_type'],
            host=data['host'],
            port=port,
            user=data['user'],
            password=data['password'],
            database=data['database'],
            schema=data.get('schema', 'public')
        )
        
        # 连接数据库
        conn.connect()
        
        # 获取表列表
        tables = conn.get_tables()
        
        # 生成连接ID并存储连接（注意：不存储密码）
        connection_id = f"conn_{datetime.now().timestamp()}"
        # 添加最后使用时间
        conn.last_used = datetime.now().timestamp()
        connections[connection_id] = conn
        
        # 保存连接ID到会话
        session['connection_id'] = connection_id
        session['db_info'] = {
            'db_type': data['db_type'],
            'host': data['host'],
            'database': data['database']
        }
        
        logger.info(f"数据库连接成功: {data['db_type']}://{data['host']}/{data['database']}")
        
        return jsonify({
            'success': True,
            'message': '数据库连接成功',
            'tables': tables,
            'count': len(tables)
        })
        
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return jsonify({'success': False, 'message': f'连接失败: {str(e)}'}), 500


@app.route('/api/table/<path:table_name>', methods=['GET'])
def api_get_table(table_name):
    """获取表结构信息"""
    try:
        # 清理过期连接
        cleanup_expired_connections(session)
        
        # 解码URL编码的表名
        table_name = unquote(table_name)
        
        # 检查连接
        if 'connection_id' not in session:
            return jsonify({'success': False, 'message': '未连接数据库'}), 401
        
        connection_id = session['connection_id']
        if connection_id not in connections:
            return jsonify({'success': False, 'message': '连接已断开'}), 401
        
        conn = connections[connection_id]
        # 更新连接使用时间
        conn.last_used = datetime.now().timestamp()
        table_structure = conn.get_table_structure(table_name)
        
        return jsonify({
            'success': True,
            'table_name': table_name,
            'fields': table_structure.get('fields', [])
        })
        
    except Exception as e:
        logger.error(f"获取表结构失败 {table_name}: {str(e)}")
        return jsonify({'success': False, 'message': f'获取表结构失败: {str(e)}'}), 500


def zip_directory(directory_path, zip_path):
    """将目录压缩成ZIP文件"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 遍历目录
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                # 构建完整的文件路径
                file_path = os.path.join(root, file)
                # 计算相对路径
                relative_path = os.path.relpath(file_path, directory_path)
                # 添加到ZIP文件
                zipf.write(file_path, relative_path)


@app.route('/api/export', methods=['POST'])
def api_export():
    """导出数据表"""
    try:
        # 清理过期连接
        cleanup_expired_connections(session)
        
        data = request.get_json()
        
        # 验证必填字段
        if 'tables' not in data or not data['tables']:
            return jsonify({'success': False, 'message': '请选择要导出的表'}), 400
        
        export_format = data.get('format', 'both')  # csv, excel, both
        
        # 检查连接
        if 'connection_id' not in session:
            return jsonify({'success': False, 'message': '未连接数据库'}), 401
        
        connection_id = session['connection_id']
        if connection_id not in connections:
            return jsonify({'success': False, 'message': '连接已断开'}), 401
        
        conn = connections[connection_id]
        # 更新连接使用时间
        conn.last_used = datetime.now().timestamp()
        db_info = session.get('db_info', {})
        
        selected_tables = data['tables']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        result = {
            'success': True,
            'message': '导出完成',
            'files': []
        }
        
        # 导出CSV
        if export_format in ['csv', 'both']:
            csv_exporter = CSVExporter(conn)
            csv_dir = os.path.join(OUTPUT_DIR, f'csv_{timestamp}')
            csv_exporter.export_by_module(csv_dir, {'all': selected_tables})
            
            # 将CSV目录打包成ZIP
            csv_zip_path = os.path.join(OUTPUT_DIR, f'csv_{timestamp}.zip')
            zip_directory(csv_dir, csv_zip_path)
            
            result['files'].append({
                'name': f'CSV文件包 ({len(selected_tables)} 个表).zip',
                'path': f'/download/csv_{timestamp}.zip',
                'type': 'file'
            })
        
        # 导出Excel
        if export_format in ['excel', 'both']:
            excel_exporter = ExcelExporter(conn)
            excel_file = excel_exporter.export_selected_tables(OUTPUT_DIR, selected_tables, show_progress=False)
            excel_filename = os.path.basename(excel_file)
            result['files'].append({
                'name': excel_filename,
                'path': f'/download/{excel_filename}',
                'type': 'file'
            })
        
        logger.info(f"导出成功: {len(selected_tables)} 个表，格式: {export_format}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"导出失败: {str(e)}")
        return jsonify({'success': False, 'message': f'导出失败: {str(e)}'}), 500


@app.route('/download/<path:filename>')
def download_file(filename):
    """下载导出的文件"""
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


@app.route('/api/disconnect', methods=['POST'])
def api_disconnect():
    """断开数据库连接"""
    try:
        if 'connection_id' in session:
            connection_id = session['connection_id']
            if connection_id in connections:
                try:
                    connections[connection_id].disconnect()
                except:
                    pass
                del connections[connection_id]
            session.pop('connection_id', None)
            session.pop('db_info', None)
        
        return jsonify({'success': True, 'message': '已断开连接'})
        
    except Exception as e:
        logger.error(f"断开连接失败: {str(e)}")
        return jsonify({'success': False, 'message': f'断开连接失败: {str(e)}'}), 500


@app.route('/api/db_info', methods=['GET'])
def api_db_info():
    """获取当前连接信息"""
    if 'db_info' in session:
        return jsonify({'success': True, 'db_info': session['db_info']})
    return jsonify({'success': False, 'message': '未连接数据库'}), 401


@app.errorhandler(404)
def not_found(error):
    return render_template('index.html', error="页面未找到"), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': '服务器内部错误'}), 500


if __name__ == '__main__':
    # 确保会话目录存在
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

    # debug模式通过环境变量控制，默认为False
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes']
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
