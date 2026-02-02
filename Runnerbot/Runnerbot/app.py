import os
import json
import threading
import re
import time
import uuid
from datetime import datetime
from typing import Any, Optional
from flask import Flask, request, jsonify, send_from_directory, Response
from werkzeug.utils import secure_filename

try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    Llama = None
    LLAMA_AVAILABLE = False

BASE_DIR = os.environ.get('RUNNERBOT_HOME', os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 * 1024

MODELS_DIR = os.path.join(BASE_DIR, 'models')
LIBRARY_DIR = os.path.join(BASE_DIR, 'library')
DATA_DIR = os.path.join(BASE_DIR, 'data')
MEMORY_FILE = os.path.join(DATA_DIR, 'memory.json')
SKILLS_FILE = os.path.join(DATA_DIR, 'skills.json')
AGENTS_FILE = os.path.join(DATA_DIR, 'agents.json')
CHAT_HISTORY_FILE = os.path.join(DATA_DIR, 'chat_history.json')
PROVIDERS_FILE = os.path.join(DATA_DIR, 'providers.json')
FILES_ROOT = BASE_DIR

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(LIBRARY_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

loaded_models: dict[str, Any] = {}
current_model: Optional[Any] = None
current_model_name: Optional[str] = None
model_lock = threading.Lock()

library_documents: dict[str, str] = {}

ALLOWED_EXTENSIONS = {'gguf', 'bin'}
LIBRARY_EXTENSIONS = {'txt', 'md', 'py', 'js', 'ts', 'html', 'css', 'json', 'csv', 'xml', 'yaml', 'yml', 'c', 'cpp', 'h', 'java', 'rs', 'go', 'sh', 'bat', 'sql', 'r', 'lua'}

def load_json_file(filepath, default=None):
    if default is None:
        default = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json_file(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

memory_store = load_json_file(MEMORY_FILE, {'facts': [], 'context': ''})
skills_store = load_json_file(SKILLS_FILE, {'skills': []})
agents_store = load_json_file(AGENTS_FILE, {'agents': []})
chat_history = load_json_file(CHAT_HISTORY_FILE, {'conversations': []})
providers_store = load_json_file(PROVIDERS_FILE, {
    'providers': [],
    'active_provider': None
})

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_library_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in LIBRARY_EXTENSIONS

def load_library():
    global library_documents
    library_documents = {}
    for filename in os.listdir(LIBRARY_DIR):
        filepath = os.path.join(LIBRARY_DIR, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    library_documents[filename] = f.read()
            except Exception:
                pass

load_library()

@app.route('/')
@app.route('/index.html')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/download')
def landing():
    return send_from_directory('.', 'landing.html')

@app.route('/api/models', methods=['GET'])
def list_models():
    models = []
    for filename in os.listdir(MODELS_DIR):
        if allowed_file(filename):
            filepath = os.path.join(MODELS_DIR, filename)
            size = os.path.getsize(filepath)
            models.append({
                'name': filename,
                'size': size,
                'size_formatted': f"{size / (1024**3):.2f} GB",
                'loaded': filename == current_model_name
            })
    return jsonify({'models': models, 'current_model': current_model_name})

@app.route('/api/models/upload', methods=['POST'])
def upload_model():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename or not allowed_file(file.filename):
        return jsonify({'error': 'Only GGUF and BIN files are supported'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(MODELS_DIR, filename)
    
    file.save(filepath)
    size = os.path.getsize(filepath)
    
    return jsonify({
        'success': True,
        'model': {
            'name': filename,
            'size': size,
            'size_formatted': f"{size / (1024**3):.2f} GB"
        }
    })

@app.route('/api/models/load', methods=['POST'])
def load_model():
    global current_model, current_model_name
    
    if not LLAMA_AVAILABLE:
        return jsonify({'error': 'llama-cpp-python is not installed. Model loading is not available.'}), 503
    
    data = request.get_json()
    model_name = data.get('model_name')
    
    if not model_name:
        return jsonify({'error': 'Model name required'}), 400
    
    filepath = os.path.join(MODELS_DIR, model_name)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Model not found'}), 404
    
    try:
        with model_lock:
            if current_model:
                del current_model
                current_model = None
            
            n_ctx = data.get('n_ctx', 2048)
            n_gpu_layers = data.get('n_gpu_layers', 0)
            
            current_model = Llama(
                model_path=filepath,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            current_model_name = model_name
        
        return jsonify({
            'success': True,
            'model_name': model_name,
            'message': f'Model {model_name} loaded successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/unload', methods=['POST'])
def unload_model():
    global current_model, current_model_name
    
    with model_lock:
        if current_model:
            del current_model
            current_model = None
            current_model_name = None
    
    return jsonify({'success': True, 'message': 'Model unloaded'})

@app.route('/api/models/delete', methods=['POST'])
def delete_model():
    global current_model, current_model_name
    
    data = request.get_json()
    model_name = data.get('model_name')
    
    if not model_name:
        return jsonify({'error': 'Model name required'}), 400
    
    filepath = os.path.join(MODELS_DIR, model_name)
    if not os.path.exists(filepath):
        return jsonify({'error': 'Model not found'}), 404
    
    with model_lock:
        if current_model_name == model_name:
            del current_model
            current_model = None
            current_model_name = None
    
    os.remove(filepath)
    return jsonify({'success': True, 'message': f'Model {model_name} deleted'})

@app.route('/api/chat', methods=['POST'])
def chat():
    global current_model, providers_store
    
    data = request.get_json()
    messages = data.get('messages', [])
    
    if not messages:
        return jsonify({'error': 'No messages provided'}), 400
    
    # Try local model first, then fall back to external provider
    if not current_model:
        # Check for active external provider
        active_id = providers_store.get('active_provider')
        if active_id:
            provider = next((p for p in providers_store['providers'] if p.get('id') == active_id), None)
            if provider:
                try:
                    response_text = call_external_provider(messages, provider)
                    return jsonify({
                        'success': True,
                        'response': response_text,
                        'provider': provider.get('name')
                    })
                except Exception as e:
                    return jsonify({'error': f"Provider error: {str(e)}"}), 500
        return jsonify({'error': 'No model loaded and no provider active'}), 400
    
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 2048)
    top_p = data.get('top_p', 0.9)
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )
        
        return jsonify({
            'success': True,
            'response': response['choices'][0]['message']['content'],
            'usage': response.get('usage', {})
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    global current_model
    
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    messages = data.get('messages', [])
    
    if not messages:
        return jsonify({'error': 'No messages provided'}), 400
    
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 2048)
    top_p = data.get('top_p', 0.9)
    
    def generate():
        try:
            with model_lock:
                stream = current_model.create_chat_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    stream=True
                )
                
                for chunk in stream:
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            yield f"data: {json.dumps({'content': content})}\n\n"
                
                yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/generate', methods=['POST'])
def generate_text():
    global current_model
    
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 2048)
    top_p = data.get('top_p', 0.9)
    
    try:
        with model_lock:
            response = current_model(
                prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )
        
        return jsonify({
            'success': True,
            'text': response['choices'][0]['text'],
            'usage': response.get('usage', {})
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def status():
    active_provider_name = None
    active_id = providers_store.get('active_provider')
    if active_id:
        provider = next((p for p in providers_store['providers'] if p.get('id') == active_id), None)
        if provider:
            active_provider_name = provider.get('name')
    
    return jsonify({
        'status': 'running',
        'model_loaded': current_model is not None,
        'current_model': current_model_name,
        'models_directory': MODELS_DIR,
        'library_count': len(library_documents),
        'active_provider': active_provider_name
    })

@app.route('/api/code/generate', methods=['POST'])
def generate_code():
    global current_model
    
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    description = data.get('description', '')
    language = data.get('language', 'python')
    
    if not description:
        return jsonify({'error': 'No description provided'}), 400
    
    prompt = f"""You are an expert programmer. Generate clean, well-commented {language} code based on the following description.

Description: {description}

Provide only the code, properly formatted with comments explaining key parts. Do not include markdown code blocks."""
    
    temperature = data.get('temperature', 0.3)
    max_tokens = data.get('max_tokens', 2048)
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": f"You are an expert {language} programmer. Generate clean, working code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9
            )
        
        code = response['choices'][0]['message']['content']
        return jsonify({
            'success': True,
            'code': code,
            'language': language
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/code/explain', methods=['POST'])
def explain_code():
    global current_model
    
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    code = data.get('code', '')
    
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a programming teacher. Explain code clearly and thoroughly."},
                    {"role": "user", "content": f"Explain this code step by step:\n\n{code}"}
                ],
                temperature=0.5,
                max_tokens=2048,
                top_p=0.9
            )
        
        explanation = response['choices'][0]['message']['content']
        return jsonify({
            'success': True,
            'explanation': explanation
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/code/debug', methods=['POST'])
def debug_code():
    global current_model
    
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    code = data.get('code', '')
    error = data.get('error', '')
    
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    
    prompt = f"Debug and fix this code:\n\n{code}"
    if error:
        prompt += f"\n\nError message: {error}"
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert debugger. Find and fix bugs in code. Provide the corrected code with explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2048,
                top_p=0.9
            )
        
        fix = response['choices'][0]['message']['content']
        return jsonify({
            'success': True,
            'fix': fix
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/code/refactor', methods=['POST'])
def refactor_code():
    global current_model
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    code = data.get('code', '')
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert software architect. Refactor code to improve readability, maintainability, and structure without changing functionality."},
                    {"role": "user", "content": f"Refactor this code to be cleaner and more maintainable. Explain what you changed and why:\n\n{code}"}
                ],
                temperature=0.3,
                max_tokens=2048,
                top_p=0.9
            )
        result = response['choices'][0]['message']['content']
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/code/optimize', methods=['POST'])
def optimize_code():
    global current_model
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    code = data.get('code', '')
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a performance optimization expert. Optimize code for speed, memory efficiency, and best practices."},
                    {"role": "user", "content": f"Optimize this code for better performance. Explain the optimizations:\n\n{code}"}
                ],
                temperature=0.3,
                max_tokens=2048,
                top_p=0.9
            )
        result = response['choices'][0]['message']['content']
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/code/document', methods=['POST'])
def document_code():
    global current_model
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    code = data.get('code', '')
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a technical documentation expert. Add comprehensive comments and docstrings to code."},
                    {"role": "user", "content": f"Add detailed comments, docstrings, and documentation to this code. Include parameter descriptions and return value documentation:\n\n{code}"}
                ],
                temperature=0.3,
                max_tokens=2048,
                top_p=0.9
            )
        result = response['choices'][0]['message']['content']
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/code/convert', methods=['POST'])
def convert_code():
    global current_model
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    code = data.get('code', '')
    target_language = data.get('target_language', 'python')
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": f"You are a polyglot programmer expert in all programming languages. Convert code to {target_language} following best practices."},
                    {"role": "user", "content": f"Convert this code to {target_language}. Ensure the converted code is idiomatic and follows {target_language} conventions:\n\n{code}"}
                ],
                temperature=0.3,
                max_tokens=2048,
                top_p=0.9
            )
        result = response['choices'][0]['message']['content']
        return jsonify({'success': True, 'result': result, 'target_language': target_language})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/code/complete', methods=['POST'])
def complete_code():
    global current_model
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    code = data.get('code', '')
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert programmer. Complete the given code intelligently, continuing the pattern and logic."},
                    {"role": "user", "content": f"Complete this code. Continue where it leaves off, maintaining the same style and logic:\n\n{code}"}
                ],
                temperature=0.4,
                max_tokens=2048,
                top_p=0.9
            )
        result = response['choices'][0]['message']['content']
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/code/review', methods=['POST'])
def review_code():
    global current_model
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    code = data.get('code', '')
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a senior code reviewer. Provide thorough code reviews covering bugs, security issues, performance problems, and style improvements."},
                    {"role": "user", "content": f"Review this code thoroughly. Check for bugs, security issues, performance problems, and suggest improvements:\n\n{code}"}
                ],
                temperature=0.4,
                max_tokens=2048,
                top_p=0.9
            )
        result = response['choices'][0]['message']['content']
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/code/tests', methods=['POST'])
def generate_tests():
    global current_model
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    code = data.get('code', '')
    language = data.get('language', 'python')
    if not code:
        return jsonify({'error': 'No code provided'}), 400
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": f"You are a test automation expert. Generate comprehensive unit tests for {language} code."},
                    {"role": "user", "content": f"Generate comprehensive unit tests for this {language} code. Include edge cases, error handling tests, and assertions:\n\n{code}"}
                ],
                temperature=0.3,
                max_tokens=2048,
                top_p=0.9
            )
        result = response['choices'][0]['message']['content']
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/code/edit', methods=['POST'])
def edit_code():
    global current_model
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    code = data.get('code', '')
    instruction = data.get('instruction', '')
    if not code or not instruction:
        return jsonify({'error': 'Code and instruction required'}), 400
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are an expert programmer. Edit code according to the user's instructions precisely."},
                    {"role": "user", "content": f"Edit this code according to the instruction.\n\nInstruction: {instruction}\n\nCode:\n{code}"}
                ],
                temperature=0.3,
                max_tokens=2048,
                top_p=0.9
            )
        result = response['choices'][0]['message']['content']
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/library', methods=['GET'])
def list_library():
    files = []
    for filename in os.listdir(LIBRARY_DIR):
        filepath = os.path.join(LIBRARY_DIR, filename)
        if os.path.isfile(filepath):
            size = os.path.getsize(filepath)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            files.append({
                'name': filename,
                'size': size,
                'size_formatted': f"{size / 1024:.1f} KB" if size > 1024 else f"{size} bytes",
                'type': ext,
                'indexed': filename in library_documents
            })
    return jsonify({'files': files, 'total': len(files)})

@app.route('/api/library/upload', methods=['POST'])
def upload_library_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    if not allowed_library_file(file.filename):
        return jsonify({'error': 'Unsupported file type. Allowed: txt, md, py, js, ts, html, css, json, csv, xml, yaml, c, cpp, java, rs, go, sh, sql'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(LIBRARY_DIR, filename)
    
    file.save(filepath)
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            library_documents[filename] = f.read()
    except Exception:
        pass
    
    size = os.path.getsize(filepath)
    
    return jsonify({
        'success': True,
        'file': {
            'name': filename,
            'size': size,
            'size_formatted': f"{size / 1024:.1f} KB" if size > 1024 else f"{size} bytes"
        }
    })

@app.route('/api/library/delete', methods=['POST'])
def delete_library_file():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'error': 'Filename required'}), 400
    
    filepath = os.path.join(LIBRARY_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    os.remove(filepath)
    if filename in library_documents:
        del library_documents[filename]
    
    return jsonify({'success': True, 'message': f'File {filename} deleted'})

@app.route('/api/library/search', methods=['POST'])
def search_library():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    query = data.get('query', '').lower()
    
    if not query:
        return jsonify({'error': 'No search query provided'}), 400
    
    results = []
    for filename, content in library_documents.items():
        content_lower = content.lower()
        if query in content_lower:
            matches = []
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if query in line.lower():
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)
                    context = '\n'.join(lines[start:end])
                    matches.append({
                        'line': i + 1,
                        'context': context[:500]
                    })
                    if len(matches) >= 5:
                        break
            
            results.append({
                'filename': filename,
                'matches': matches,
                'total_matches': content_lower.count(query)
            })
    
    results.sort(key=lambda x: x['total_matches'], reverse=True)
    
    return jsonify({
        'success': True,
        'query': query,
        'results': results[:20],
        'total_files': len(results)
    })

@app.route('/api/library/read', methods=['POST'])
def read_library_file():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'error': 'Filename required'}), 400
    
    if filename not in library_documents:
        filepath = os.path.join(LIBRARY_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    library_documents[filename] = f.read()
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'error': 'File not found'}), 404
    
    content = library_documents.get(filename, '')
    return jsonify({
        'success': True,
        'filename': filename,
        'content': content[:50000],
        'truncated': len(content) > 50000
    })

@app.route('/api/library/learn', methods=['POST'])
def learn_from_library():
    global current_model
    
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    question = data.get('question', '')
    files = data.get('files', [])
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    context = ""
    if files:
        for filename in files[:5]:
            if filename in library_documents:
                content = library_documents[filename][:5000]
                context += f"\n--- {filename} ---\n{content}\n"
    else:
        for filename, content in list(library_documents.items())[:3]:
            context += f"\n--- {filename} ---\n{content[:3000]}\n"
    
    if not context:
        return jsonify({'error': 'No library files available. Please upload some files first.'}), 400
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": "You are a helpful learning assistant. Use the provided reference materials to answer questions. Cite specific parts of the documents when relevant."},
                    {"role": "user", "content": f"Reference materials:\n{context}\n\nQuestion: {question}"}
                ],
                temperature=0.5,
                max_tokens=2048,
                top_p=0.9
            )
        
        answer = response['choices'][0]['message']['content']
        return jsonify({
            'success': True,
            'answer': answer,
            'sources': list(library_documents.keys())[:5]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/library/teach', methods=['POST'])
def teach_from_library():
    global current_model
    
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    topic = data.get('topic', '')
    level = data.get('level', 'beginner')
    style = data.get('style', 'friendly')
    
    if not topic:
        return jsonify({'error': 'No topic provided'}), 400
    
    context = ""
    for filename, content in list(library_documents.items())[:3]:
        context += f"\n--- {filename} ---\n{content[:3000]}\n"
    
    teacher_personas = {
        'friendly': "You are a warm, encouraging teacher who makes learning fun. Use simple language, real-world examples, and celebrate progress. Ask follow-up questions to check understanding.",
        'strict': "You are a rigorous, disciplined teacher who maintains high standards. Be precise, structured, and thorough. Correct mistakes firmly but fairly. Focus on accuracy and proper terminology.",
        'socratic': "You are a Socratic teacher who guides through questions. Instead of giving direct answers, ask thought-provoking questions that lead students to discover the answer themselves.",
        'storyteller': "You are a teacher who explains everything through stories and narratives. Create memorable analogies and weave concepts into engaging tales that make abstract ideas concrete."
    }
    
    level_instructions = {
        'beginner': "Explain as if teaching a complete beginner. Use no jargon. Start with the absolute basics.",
        'intermediate': "Explain for someone with basic knowledge. Build on fundamentals and introduce more complex ideas.",
        'advanced': "Explain for someone with solid knowledge. Go deep into nuances, edge cases, and advanced concepts.",
        'expert': "Discuss at an expert level. Assume deep knowledge and focus on cutting-edge ideas and subtle distinctions."
    }
    
    persona = teacher_personas.get(style, teacher_personas['friendly'])
    level_guide = level_instructions.get(level, level_instructions['beginner'])
    
    system_prompt = f"""{persona}

{level_guide}

You are teaching about: {topic}

Teaching guidelines:
- Break down complex concepts into digestible parts
- Use bullet points and numbered lists for clarity
- Include examples and analogies
- Summarize key takeaways at the end
- Keep responses clear and well-organized for text-to-speech reading"""
    
    if context:
        system_prompt += f"\n\nYou have these reference materials to draw from:\n{context}"
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please teach me about: {topic}"}
                ],
                temperature=0.7,
                max_tokens=2048,
                top_p=0.9
            )
        
        lesson = response['choices'][0]['message']['content']
        return jsonify({
            'success': True,
            'lesson': lesson,
            'topic': topic,
            'level': level,
            'style': style
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ MEMORY API ============
@app.route('/api/memory', methods=['GET'])
def get_memory():
    return jsonify(memory_store)

@app.route('/api/memory/add', methods=['POST'])
def add_memory():
    global memory_store
    data = request.get_json()
    fact = data.get('fact', '').strip()
    if fact:
        memory_store['facts'].append({
            'id': str(uuid.uuid4()),
            'fact': fact,
            'timestamp': datetime.now().isoformat()
        })
        save_json_file(MEMORY_FILE, memory_store)
    return jsonify({'success': True, 'memory': memory_store})

@app.route('/api/memory/context', methods=['POST'])
def set_context():
    global memory_store
    data = request.get_json()
    memory_store['context'] = data.get('context', '')
    save_json_file(MEMORY_FILE, memory_store)
    return jsonify({'success': True})

@app.route('/api/memory/clear', methods=['POST'])
def clear_memory():
    global memory_store
    memory_store = {'facts': [], 'context': ''}
    save_json_file(MEMORY_FILE, memory_store)
    return jsonify({'success': True})

@app.route('/api/memory/delete', methods=['POST'])
def delete_memory():
    global memory_store
    data = request.get_json()
    fact_id = data.get('id')
    memory_store['facts'] = [f for f in memory_store['facts'] if f.get('id') != fact_id]
    save_json_file(MEMORY_FILE, memory_store)
    return jsonify({'success': True, 'memory': memory_store})

# ============ SKILLS API ============
@app.route('/api/skills', methods=['GET'])
def get_skills():
    return jsonify(skills_store)

@app.route('/api/skills/create', methods=['POST'])
def create_skill():
    global skills_store
    data = request.get_json()
    skill = {
        'id': str(uuid.uuid4()),
        'name': data.get('name', 'Unnamed Skill'),
        'description': data.get('description', ''),
        'prompt': data.get('prompt', ''),
        'created': datetime.now().isoformat()
    }
    skills_store['skills'].append(skill)
    save_json_file(SKILLS_FILE, skills_store)
    return jsonify({'success': True, 'skill': skill})

@app.route('/api/skills/execute', methods=['POST'])
def execute_skill():
    global current_model
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    skill_id = data.get('skill_id')
    user_input = data.get('input', '')
    
    skill = next((s for s in skills_store['skills'] if s['id'] == skill_id), None)
    if not skill:
        return jsonify({'error': 'Skill not found'}), 404
    
    prompt = skill['prompt'].replace('{input}', user_input)
    
    memory_context = ""
    if memory_store['facts']:
        memory_context = "Known facts:\n" + "\n".join([f"- {f['fact']}" for f in memory_store['facts'][-10:]]) + "\n\n"
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": f"{memory_context}You are an AI assistant executing a skill: {skill['name']}. {skill['description']}"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2048
            )
        return jsonify({
            'success': True,
            'result': response['choices'][0]['message']['content'],
            'skill': skill['name']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skills/delete', methods=['POST'])
def delete_skill():
    global skills_store
    data = request.get_json()
    skill_id = data.get('id')
    skills_store['skills'] = [s for s in skills_store['skills'] if s['id'] != skill_id]
    save_json_file(SKILLS_FILE, skills_store)
    return jsonify({'success': True})

# ============ AGENTS API ============
@app.route('/api/agents', methods=['GET'])
def get_agents():
    return jsonify(agents_store)

@app.route('/api/agents/create', methods=['POST'])
def create_agent():
    global agents_store
    data = request.get_json()
    agent = {
        'id': str(uuid.uuid4()),
        'name': data.get('name', 'New Agent'),
        'persona': data.get('persona', 'You are a helpful AI assistant.'),
        'skills': data.get('skills', []),
        'created': datetime.now().isoformat()
    }
    agents_store['agents'].append(agent)
    save_json_file(AGENTS_FILE, agents_store)
    return jsonify({'success': True, 'agent': agent})

@app.route('/api/agents/chat', methods=['POST'])
def chat_with_agent():
    global current_model
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    agent_id = data.get('agent_id')
    message = data.get('message', '')
    
    agent = next((a for a in agents_store['agents'] if a['id'] == agent_id), None)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    memory_context = ""
    if memory_store['facts']:
        memory_context = "\n\nKnown facts about the user:\n" + "\n".join([f"- {f['fact']}" for f in memory_store['facts'][-10:]])
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=[
                    {"role": "system", "content": f"{agent['persona']}{memory_context}"},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=2048
            )
        return jsonify({
            'success': True,
            'response': response['choices'][0]['message']['content'],
            'agent': agent['name']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents/delete', methods=['POST'])
def delete_agent():
    global agents_store
    data = request.get_json()
    agent_id = data.get('id')
    agents_store['agents'] = [a for a in agents_store['agents'] if a['id'] != agent_id]
    save_json_file(AGENTS_FILE, agents_store)
    return jsonify({'success': True})

# ============ FILE BROWSER API ============
def is_safe_path(path):
    try:
        abs_path = os.path.realpath(os.path.abspath(path))
        return os.path.commonpath([FILES_ROOT, abs_path]) == FILES_ROOT
    except ValueError:
        return False

@app.route('/api/files', methods=['GET'])
def browse_files():
    path = request.args.get('path', '.')
    try:
        safe_path = os.path.abspath(path)
        if not is_safe_path(safe_path):
            return jsonify({'error': 'Access denied: Path outside project directory'}), 403
        if not os.path.exists(safe_path):
            return jsonify({'error': 'Path not found'}), 404
        
        items = []
        for item in os.listdir(safe_path):
            if item.startswith('.'):
                continue
            item_path = os.path.join(safe_path, item)
            is_dir = os.path.isdir(item_path)
            try:
                size = os.path.getsize(item_path) if not is_dir else 0
            except:
                size = 0
            items.append({
                'name': item,
                'path': item_path,
                'is_directory': is_dir,
                'size': size,
                'size_formatted': f"{size / 1024:.1f} KB" if size > 0 else ''
            })
        
        items.sort(key=lambda x: (not x['is_directory'], x['name'].lower()))
        return jsonify({
            'path': safe_path,
            'parent': os.path.dirname(safe_path) if safe_path != FILES_ROOT else safe_path,
            'items': items
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/read', methods=['POST'])
def read_file():
    data = request.get_json()
    filepath = data.get('path', '')
    try:
        safe_path = os.path.abspath(filepath)
        if not is_safe_path(safe_path):
            return jsonify({'error': 'Access denied: Path outside project directory'}), 403
        if not os.path.exists(safe_path):
            return jsonify({'error': 'File not found'}), 404
        if os.path.isdir(safe_path):
            return jsonify({'error': 'Cannot read directory'}), 400
        
        with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(100000)
        
        return jsonify({'success': True, 'content': content, 'path': safe_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/ai-search', methods=['POST'])
def ai_search_files():
    global current_model, providers_store
    data = request.get_json()
    query = data.get('query', '')
    search_path = data.get('path', '.')
    
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    try:
        safe_path = os.path.abspath(search_path)
        if not is_safe_path(safe_path):
            return jsonify({'error': 'Access denied'}), 403
        
        files_info = []
        text_extensions = {'.py', '.js', '.ts', '.html', '.css', '.json', '.md', '.txt', '.yaml', '.yml', '.sh', '.bat', '.sql', '.xml', '.ini', '.cfg', '.env', '.jsx', '.tsx', '.vue', '.svelte'}
        
        for root, dirs, files in os.walk(safe_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'node_modules', '__pycache__', 'venv', '.git'}]
            
            for filename in files[:100]:
                if filename.startswith('.'):
                    continue
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, safe_path)
                ext = os.path.splitext(filename)[1].lower()
                
                preview = ""
                if ext in text_extensions:
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            preview = f.read(500)
                    except:
                        pass
                
                files_info.append({
                    'path': rel_path,
                    'name': filename,
                    'preview': preview[:200] if preview else f"[{ext or 'binary'} file]"
                })
            
            if len(files_info) >= 50:
                break
        
        if not files_info:
            return jsonify({'results': [], 'message': 'No files found in directory'})
        
        files_summary = "\n".join([f"- {f['path']}: {f['preview'][:100]}..." for f in files_info[:30]])
        
        prompt = f"""Analyze these files and find the ones most relevant to this search query: "{query}"

Files in directory:
{files_summary}

Return a JSON array of the most relevant file paths (max 10), with a brief reason for each. Format:
[{{"path": "file/path.ext", "reason": "why this file matches"}}]

Only return the JSON array, no other text."""

        if current_model:
            result = current_model(prompt, max_tokens=500, temperature=0.3)
            response_text = result['choices'][0]['text'] if 'choices' in result else str(result)
        else:
            active_id = providers_store.get('active_provider')
            if active_id:
                provider = next((p for p in providers_store['providers'] if p.get('id') == active_id), None)
                if provider:
                    response_text = call_external_provider(provider, prompt)
                else:
                    return jsonify({'error': 'No AI model loaded and no active provider'}), 400
            else:
                return jsonify({'error': 'No AI model loaded. Load a model or configure an external provider first.'}), 400
        
        try:
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group())
                return jsonify({'results': results[:10], 'query': query})
        except:
            pass
        
        return jsonify({'results': [], 'raw_response': response_text, 'message': 'Could not parse AI response'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def call_external_provider(provider, prompt):
    import requests
    provider_type = provider.get('type', 'openai')
    token = provider.get('token', '')
    model = provider.get('model', '')
    endpoint = provider.get('endpoint', '')
    
    if provider_type == 'openai':
        url = endpoint or 'https://api.openai.com/v1/chat/completions'
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        payload = {'model': model or 'gpt-3.5-turbo', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 500}
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
    elif provider_type == 'anthropic':
        url = endpoint or 'https://api.anthropic.com/v1/messages'
        headers = {'x-api-key': token, 'Content-Type': 'application/json', 'anthropic-version': '2023-06-01'}
        payload = {'model': model or 'claude-3-haiku-20240307', 'max_tokens': 500, 'messages': [{'role': 'user', 'content': prompt}]}
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        return response.json().get('content', [{}])[0].get('text', '')
    elif provider_type == 'xai':
        url = endpoint or 'https://api.x.ai/v1/chat/completions'
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        payload = {'model': model or 'grok-beta', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 500}
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
    else:
        url = endpoint
        if not url:
            return 'No endpoint configured'
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        payload = {'model': model, 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 500}
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')

# ============ CHAT HISTORY API ============
@app.route('/api/history', methods=['GET'])
def get_chat_history():
    return jsonify(chat_history)

@app.route('/api/history/save', methods=['POST'])
def save_chat_history():
    global chat_history
    data = request.get_json()
    messages = data.get('messages', [])
    if messages:
        chat_history['conversations'].append({
            'id': len(chat_history['conversations']) + 1,
            'messages': messages,
            'timestamp': datetime.now().isoformat()
        })
        if len(chat_history['conversations']) > 50:
            chat_history['conversations'] = chat_history['conversations'][-50:]
        save_json_file(CHAT_HISTORY_FILE, chat_history)
    return jsonify({'success': True})

@app.route('/api/history/clear', methods=['POST'])
def clear_chat_history():
    global chat_history
    chat_history = {'conversations': []}
    save_json_file(CHAT_HISTORY_FILE, chat_history)
    return jsonify({'success': True})

# ============ ENHANCED CHAT WITH MEMORY ============
@app.route('/api/chat/memory', methods=['POST'])
def chat_with_memory():
    global current_model
    if not current_model:
        return jsonify({'error': 'No model loaded'}), 400
    
    data = request.get_json()
    messages = data.get('messages', [])
    
    if not messages:
        return jsonify({'error': 'No messages provided'}), 400
    
    memory_context = ""
    if memory_store['facts']:
        memory_context = "Known facts about the user:\n" + "\n".join([f"- {f['fact']}" for f in memory_store['facts'][-15:]]) + "\n\n"
    if memory_store['context']:
        memory_context += f"Context: {memory_store['context']}\n\n"
    
    enhanced_messages = messages.copy()
    if enhanced_messages and enhanced_messages[0]['role'] == 'system':
        enhanced_messages[0]['content'] = memory_context + enhanced_messages[0]['content']
    else:
        enhanced_messages.insert(0, {'role': 'system', 'content': memory_context + 'You are a helpful AI assistant with persistent memory.'})
    
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens', 2048)
    
    try:
        with model_lock:
            response = current_model.create_chat_completion(
                messages=enhanced_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
        return jsonify({
            'success': True,
            'response': response['choices'][0]['message']['content']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ NETWORK SETTINGS API ============
NETWORK_FILE = os.path.join(DATA_DIR, 'network.json')
network_config = load_json_file(NETWORK_FILE, {
    'host': '0.0.0.0',
    'port': 5000,
    'tunnel_enabled': False,
    'tunnel_service': 'none',
    'tunnel_authtoken': '',
    'tunnel_url': ''
})

tunnel_process = None

@app.route('/api/network', methods=['GET'])
def get_network_config():
    config = network_config.copy()
    config['tunnel_authtoken'] = '***' if config.get('tunnel_authtoken') else ''
    return jsonify(config)

@app.route('/api/network/save', methods=['POST'])
def save_network_config():
    global network_config
    data = request.get_json()
    
    network_config['host'] = data.get('host', '0.0.0.0')
    network_config['port'] = int(data.get('port', 5000))
    network_config['tunnel_service'] = data.get('tunnel_service', 'none')
    
    if data.get('tunnel_authtoken') and data.get('tunnel_authtoken') != '***':
        network_config['tunnel_authtoken'] = data.get('tunnel_authtoken', '')
    
    save_json_file(NETWORK_FILE, network_config)
    return jsonify({'success': True, 'message': 'Settings saved. Restart server to apply port/host changes.'})

@app.route('/api/network/mesh/save', methods=['POST'])
def save_mesh_config():
    global network_config
    data = request.get_json()
    
    network_config['mesh_type'] = data.get('mesh_type', 'none')
    network_config['mesh_host'] = data.get('mesh_host', '')
    network_config['mesh_port'] = int(data.get('mesh_port', 5000))
    network_config['mesh_custom_url'] = data.get('mesh_custom_url', '')
    network_config['mesh_network_id'] = data.get('mesh_network_id', '')
    
    save_json_file(NETWORK_FILE, network_config)
    return jsonify({'success': True, 'message': 'Mesh settings saved.'})

@app.route('/api/network/vpn/save', methods=['POST'])
def save_vpn_config():
    global network_config
    data = request.get_json()
    
    network_config['vpn_provider'] = data.get('vpn_provider', 'none')
    network_config['vpn_server'] = data.get('vpn_server', '')
    network_config['vpn_username'] = data.get('vpn_username', '')
    network_config['vpn_config_path'] = data.get('vpn_config_path', '')
    
    if data.get('vpn_password') and data.get('vpn_password') != '***':
        network_config['vpn_password'] = data.get('vpn_password', '')
    
    save_json_file(NETWORK_FILE, network_config)
    return jsonify({'success': True, 'message': 'VPN settings saved.'})

@app.route('/api/search', methods=['POST'])
def web_search():
    import requests
    from urllib.parse import quote_plus
    
    data = request.get_json()
    query = data.get('query', '')
    engine = data.get('engine', 'duckduckgo')
    
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    try:
        results = []
        
        if engine == 'duckduckgo':
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            
            from html.parser import HTMLParser
            class DDGParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.results = []
                    self.in_result = False
                    self.current = {}
                    self.capture_title = False
                    self.capture_snippet = False
                    
                def handle_starttag(self, tag, attrs):
                    attrs_dict = dict(attrs)
                    if tag == 'a' and 'result__a' in attrs_dict.get('class', ''):
                        self.in_result = True
                        self.current = {'url': attrs_dict.get('href', ''), 'title': '', 'snippet': ''}
                        self.capture_title = True
                    elif tag == 'a' and 'result__snippet' in attrs_dict.get('class', ''):
                        self.capture_snippet = True
                        
                def handle_endtag(self, tag):
                    if tag == 'a' and self.capture_title:
                        self.capture_title = False
                    elif tag == 'a' and self.capture_snippet:
                        self.capture_snippet = False
                        if self.current.get('title'):
                            self.results.append(self.current)
                            self.current = {}
                        self.in_result = False
                        
                def handle_data(self, data):
                    if self.capture_title:
                        self.current['title'] += data.strip()
                    elif self.capture_snippet:
                        self.current['snippet'] += data.strip()
            
            parser = DDGParser()
            parser.feed(response.text)
            results = parser.results[:10]
            
        else:
            search_urls = {
                'google': f'https://www.google.com/search?q={quote_plus(query)}',
                'bing': f'https://www.bing.com/search?q={quote_plus(query)}',
                'brave': f'https://search.brave.com/search?q={quote_plus(query)}'
            }
            return jsonify({
                'results': [],
                'redirect_url': search_urls.get(engine, search_urls['google']),
                'message': f'Open in browser: {search_urls.get(engine)}'
            })
        
        return jsonify({'results': results, 'query': query, 'engine': engine})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/network/tunnel/start', methods=['POST'])
def start_tunnel():
    global tunnel_process, network_config
    
    data = request.get_json()
    service = data.get('service', network_config.get('tunnel_service', 'none'))
    authtoken = data.get('authtoken', network_config.get('tunnel_authtoken', ''))
    port = data.get('port', network_config.get('port', 5000))
    
    if service == 'none':
        return jsonify({'error': 'No tunnel service selected'}), 400
    
    try:
        import subprocess
        import shutil
        
        if service == 'ngrok':
            ngrok_path = shutil.which('ngrok')
            if not ngrok_path:
                return jsonify({'error': 'ngrok not installed. Install from ngrok.com or run: pip install pyngrok'}), 400
            
            if tunnel_process:
                tunnel_process.terminate()
            
            if authtoken:
                subprocess.run([ngrok_path, 'config', 'add-authtoken', authtoken], capture_output=True)
            
            tunnel_process = subprocess.Popen(
                [ngrok_path, 'http', str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(2)
            
            try:
                import urllib.request
                tunnels_response = urllib.request.urlopen('http://127.0.0.1:4040/api/tunnels')
                tunnels_data = json.loads(tunnels_response.read().decode())
                if tunnels_data.get('tunnels'):
                    tunnel_url = tunnels_data['tunnels'][0].get('public_url', '')
                    network_config['tunnel_url'] = tunnel_url
                    network_config['tunnel_enabled'] = True
                    save_json_file(NETWORK_FILE, network_config)
                    return jsonify({'success': True, 'url': tunnel_url})
            except:
                pass
            
            return jsonify({'success': True, 'message': 'Tunnel started. Check ngrok dashboard for URL.'})
        
        elif service == 'pinggy':
            ssh_path = shutil.which('ssh')
            if not ssh_path:
                return jsonify({'error': 'SSH not available for Pinggy tunnel'}), 400
            
            if tunnel_process:
                tunnel_process.terminate()
            
            tunnel_process = subprocess.Popen(
                [ssh_path, '-p', '443', '-R0:localhost:' + str(port), '-o', 'StrictHostKeyChecking=no', 'a.pinggy.io'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            network_config['tunnel_enabled'] = True
            save_json_file(NETWORK_FILE, network_config)
            return jsonify({'success': True, 'message': 'Pinggy tunnel starting. Check terminal for URL.'})
        
        elif service == 'localtunnel':
            lt_path = shutil.which('lt')
            if not lt_path:
                return jsonify({'error': 'localtunnel not installed. Run: npm install -g localtunnel'}), 400
            
            if tunnel_process:
                tunnel_process.terminate()
            
            tunnel_process = subprocess.Popen(
                [lt_path, '--port', str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            network_config['tunnel_enabled'] = True
            save_json_file(NETWORK_FILE, network_config)
            return jsonify({'success': True, 'message': 'LocalTunnel starting. Check terminal for URL.'})
        
        else:
            return jsonify({'error': f'Unknown service: {service}'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/network/tunnel/stop', methods=['POST'])
def stop_tunnel():
    global tunnel_process, network_config
    
    if tunnel_process:
        tunnel_process.terminate()
        tunnel_process = None
    
    network_config['tunnel_enabled'] = False
    network_config['tunnel_url'] = ''
    save_json_file(NETWORK_FILE, network_config)
    
    return jsonify({'success': True, 'message': 'Tunnel stopped'})

@app.route('/api/network/status', methods=['GET'])
def get_network_status():
    import socket
    
    local_ip = '127.0.0.1'
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        pass
    
    return jsonify({
        'local_url': f"http://{local_ip}:{network_config.get('port', 5000)}",
        'localhost_url': f"http://localhost:{network_config.get('port', 5000)}",
        'tunnel_active': tunnel_process is not None and tunnel_process.poll() is None,
        'tunnel_url': network_config.get('tunnel_url', ''),
        'host': network_config.get('host', '0.0.0.0'),
        'port': network_config.get('port', 5000)
    })

# ============ EXTERNAL AI PROVIDERS API ============
@app.route('/api/providers', methods=['GET'])
def get_providers():
    safe_providers = []
    for p in providers_store.get('providers', []):
        safe_providers.append({
            'id': p.get('id'),
            'name': p.get('name'),
            'type': p.get('type'),
            'model': p.get('model'),
            'endpoint': p.get('endpoint', ''),
            'has_token': bool(p.get('token'))
        })
    return jsonify({
        'providers': safe_providers,
        'active_provider': providers_store.get('active_provider')
    })

@app.route('/api/providers/add', methods=['POST'])
def add_provider():
    global providers_store
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name', '').strip()
    provider_type = data.get('type', '').strip()
    token = data.get('token', '').strip()
    model = data.get('model', '').strip()
    endpoint = data.get('endpoint', '').strip()
    
    if not name or not provider_type or not token:
        return jsonify({'error': 'Name, type, and token are required'}), 400
    
    provider = {
        'id': str(uuid.uuid4()),
        'name': name,
        'type': provider_type,
        'token': token,
        'model': model,
        'endpoint': endpoint
    }
    
    providers_store['providers'].append(provider)
    save_json_file(PROVIDERS_FILE, providers_store)
    
    return jsonify({'success': True, 'provider_id': provider['id']})

@app.route('/api/providers/delete', methods=['POST'])
def delete_provider():
    global providers_store
    data = request.get_json()
    provider_id = data.get('id')
    
    if not provider_id:
        return jsonify({'error': 'Provider ID required'}), 400
    
    providers_store['providers'] = [p for p in providers_store['providers'] if p.get('id') != provider_id]
    if providers_store.get('active_provider') == provider_id:
        providers_store['active_provider'] = None
    save_json_file(PROVIDERS_FILE, providers_store)
    
    return jsonify({'success': True})

@app.route('/api/providers/activate', methods=['POST'])
def activate_provider():
    global providers_store
    data = request.get_json()
    provider_id = data.get('id')
    
    providers_store['active_provider'] = provider_id
    save_json_file(PROVIDERS_FILE, providers_store)
    
    return jsonify({'success': True})

def call_external_provider(messages, provider):
    import urllib.request
    import urllib.error
    
    provider_type = provider.get('type', '')
    token = provider.get('token', '')
    model = provider.get('model', '')
    endpoint = provider.get('endpoint', '')
    
    headers = {'Content-Type': 'application/json'}
    
    if provider_type == 'openai':
        url = endpoint or 'https://api.openai.com/v1/chat/completions'
        headers['Authorization'] = f'Bearer {token}'
        payload = {'model': model or 'gpt-3.5-turbo', 'messages': messages}
    elif provider_type == 'anthropic':
        url = endpoint or 'https://api.anthropic.com/v1/messages'
        headers['x-api-key'] = token
        headers['anthropic-version'] = '2023-06-01'
        system_msg = next((m['content'] for m in messages if m['role'] == 'system'), '')
        user_msgs = [{'role': m['role'], 'content': m['content']} for m in messages if m['role'] != 'system']
        payload = {'model': model or 'claude-3-haiku-20240307', 'max_tokens': 2048, 'messages': user_msgs}
        if system_msg:
            payload['system'] = system_msg
    elif provider_type == 'ollama':
        url = endpoint or 'http://localhost:11434/api/chat'
        payload = {'model': model or 'llama2', 'messages': messages, 'stream': False}
    elif provider_type == 'xai':
        url = endpoint or 'https://api.x.ai/v1/chat/completions'
        headers['Authorization'] = f'Bearer {token}'
        payload = {'model': model or 'grok-beta', 'messages': messages}
    else:
        url = endpoint or 'https://api.openai.com/v1/chat/completions'
        headers['Authorization'] = f'Bearer {token}'
        payload = {'model': model or 'gpt-3.5-turbo', 'messages': messages}
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            
            if provider_type == 'anthropic':
                return result.get('content', [{}])[0].get('text', '')
            elif provider_type == 'ollama':
                return result.get('message', {}).get('content', '')
            else:
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        raise Exception(f"API error {e.code}: {error_body}")

@app.route('/api/providers/chat', methods=['POST'])
def chat_with_provider():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    message = data.get('message', '')
    provider_id = data.get('provider_id') or providers_store.get('active_provider')
    
    if not provider_id:
        return jsonify({'error': 'No provider selected'}), 400
    
    provider = next((p for p in providers_store['providers'] if p.get('id') == provider_id), None)
    if not provider:
        return jsonify({'error': 'Provider not found'}), 404
    
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": message}
    ]
    
    try:
        response = call_external_provider(messages, provider)
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ DOWNLOAD API ============
@app.route('/api/download', methods=['GET'])
def download_app():
    import zipfile
    import io
    
    exclude_dirs = {'venv', '__pycache__', '.git', 'node_modules', '.cache'}
    exclude_files = {'.pyc', '.pyo', '.git', '.DS_Store'}
    
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(BASE_DIR):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            rel_root = os.path.relpath(root, BASE_DIR)
            
            for file in files:
                if any(file.endswith(ext) for ext in exclude_files):
                    continue
                
                file_path = os.path.join(root, file)
                arc_name = os.path.join('Runnerbot', rel_root, file) if rel_root != '.' else os.path.join('Runnerbot', file)
                
                try:
                    zf.write(file_path, arc_name)
                except Exception:
                    pass
    
    memory_file.seek(0)
    
    return Response(
        memory_file.getvalue(),
        mimetype='application/zip',
        headers={'Content-Disposition': 'attachment; filename=Runnerbot.zip'}
    )

if __name__ == '__main__':
    host = network_config.get('host', '0.0.0.0')
    port = network_config.get('port', 5000)
    print(f"Starting Runnerbot on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
