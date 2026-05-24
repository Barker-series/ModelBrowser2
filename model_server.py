#!/usr/bin/env python3
"""
Model Gallery Server
A simple HTTP server that provides file system access for the model gallery browser.
Based on the gallery.py scanning logic but serves data via HTTP API.
"""

import os
import json
import re
import http.server
import socketserver
import urllib.parse
from pathlib import Path
import mimetypes
import datetime
import signal
import sys
import socket
from PIL import Image

# Default configuration - will be overridden by config.json if it exists
DEFAULT_MODEL_ROOT = r"C:\Chris\ComfyUI\ComfyUI\models"
DEFAULT_FOLDER_WHITELIST = [
    "Stable-diffusion",  # Checkpoint models
    "Lora",              # LoRA models
    "checkpoints"        # Checkpoint models
]

# Configuration file path
CONFIG_FILE = "config.json"

def load_config():
    """Load configuration from config.json file or return defaults"""
    global MODEL_ROOT, FOLDER_WHITELIST
    
    try:
        if os.path.exists(CONFIG_FILE):
            print(f"📖 Loading configuration from {CONFIG_FILE}")
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                MODEL_ROOT = config.get('modelRoot', DEFAULT_MODEL_ROOT)
                FOLDER_WHITELIST = config.get('folderWhitelist', DEFAULT_FOLDER_WHITELIST)
                print(f"✅ Configuration loaded: MODEL_ROOT={MODEL_ROOT}")
                print(f"✅ Configuration loaded: FOLDER_WHITELIST={FOLDER_WHITELIST}")
        else:
            print(f"📋 No config file found, using defaults")
            MODEL_ROOT = DEFAULT_MODEL_ROOT
            FOLDER_WHITELIST = DEFAULT_FOLDER_WHITELIST
    except Exception as e:
        print(f"❌ Error loading config file: {e}")
        print(f"📋 Using default configuration")
        MODEL_ROOT = DEFAULT_MODEL_ROOT
        FOLDER_WHITELIST = DEFAULT_FOLDER_WHITELIST

def save_config():
    """Save current configuration to config.json file"""
    try:
        config = {
            'modelRoot': MODEL_ROOT,
            'folderWhitelist': FOLDER_WHITELIST
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"💾 Configuration saved to {CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"❌ Error saving config file: {e}")
        return False

# Initialize configuration
MODEL_ROOT = DEFAULT_MODEL_ROOT
FOLDER_WHITELIST = DEFAULT_FOLDER_WHITELIST

class ReuseAddrTCPServer(socketserver.TCPServer):
    """TCPServer that allows address reuse to prevent 'Address already in use' errors."""
    allow_reuse_address = True
    
    def server_bind(self):
        """Override server_bind to set socket options before binding."""
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Also set SO_REUSEPORT if available (Linux/macOS)
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass  # Not available on all platforms
        super().server_bind()
    
    def server_close(self):
        """Ensure socket is properly closed."""
        super().server_close()

class ModelServerHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        print(f"🔍 DEBUG: Received GET request for: {path}")
        
        if path == '/api/scan':
            self.handle_scan_models()
        elif path.startswith('/api/image/'):
            self.handle_image_request(path)
        elif path.startswith('/api/json/'):
            self.handle_json_request(path)
        elif path == '/api/config':
            self.handle_config_request()
        elif path == '/' or path == '':
            # Serve index.html for root path
            self.serve_index_html()
        else:
            # Serve other static files (CSS, JS, images)
            self.serve_static_file(path)
    
    def do_POST(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            print(f"📝 DEBUG: Received POST request for: {path}")
            print(f"📝 DEBUG: Headers: {dict(self.headers)}")
            
            if path.startswith('/api/json/'):
                self.handle_json_save(path)
            elif path == '/api/cache-thumbnails':
                self.handle_cache_thumbnails()
            elif path == '/api/upload-thumbnail':
                self.handle_upload_thumbnail()
            elif path == '/api/open-file-explorer':
                self.handle_open_file_explorer()
            elif path == '/api/config':
                self.handle_config_save()
            else:
                print(f"📝 DEBUG: No handler for POST path: {path}")
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {
                    'success': False,
                    'error': f'No handler for POST path: {path}'
                }
                self.wfile.write(json.dumps(error_response).encode())
        except Exception as e:
            print(f"❌ DEBUG: Error in do_POST: {e}")
            import traceback
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {
                'success': False,
                'error': f'Server error in POST handler: {str(e)}'
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def serve_index_html(self):
        """Serve the index.html file"""
        print(f"🔍 DEBUG: Attempting to serve index.html from {os.getcwd()}")
        try:
            file_path = os.path.join(os.getcwd(), 'index.html')
            print(f"🔍 DEBUG: Full file path: {file_path}")
            print(f"🔍 DEBUG: File exists: {os.path.exists(file_path)}")
            
            with open('index.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"🔍 DEBUG: Read {len(content)} characters from index.html")
            print(f"🔍 DEBUG: First 100 chars: {content[:100]}...")
            
            # Send HTTP response in correct order
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content.encode('utf-8'))))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            print(f"🔍 DEBUG: Headers sent, writing content...")
            self.wfile.write(content.encode('utf-8'))
            self.wfile.flush()
            
            print(f"✅ DEBUG: Successfully served index.html")
            
        except FileNotFoundError as e:
            print(f"❌ DEBUG: FileNotFoundError: {e}")
            self.send_response(404)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            error_html = f"""<!DOCTYPE html>
            <html><body>
            <h1>404 - File Not Found</h1>
            <p>index.html not found in the current directory: {os.getcwd()}</p>
            <p>Available files: {', '.join(os.listdir('.'))}</p>
            </body></html>
            """
            self.wfile.write(error_html.encode('utf-8'))
        except Exception as e:
            print(f"❌ DEBUG: Exception: {e}")
            import traceback
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            error_html = f"<!DOCTYPE html><html><body><h1>500 - Server Error</h1><p>{str(e)}</p></body></html>"
            self.wfile.write(error_html.encode('utf-8'))
    
    def serve_static_file(self, path):
        """Serve static files like CSS, JS, images"""
        try:
            # Remove leading slash
            file_path = path.lstrip('/')
            
            # Security check - prevent directory traversal
            if '..' in file_path or file_path.startswith('/'):
                self.send_response(403)
                self.end_headers()
                return
            
            # Check if file exists
            if not os.path.exists(file_path):
                self.send_response(404)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(b'File not found')
                return
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = 'application/octet-stream'
            
            # Serve the file
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(os.path.getsize(file_path)))
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
                
        except Exception as e:
            print(f"❌ DEBUG: Error serving static file {path}: {e}")
            self.send_response(500)
            self.end_headers()
    
    def handle_scan_models(self):
        """Scan models and return hierarchical structure"""
        try:
            model_tree = self.scan_models_hierarchically(MODEL_ROOT)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': True,
                'data': model_tree,
                'root': MODEL_ROOT,
                'whitelist': FOLDER_WHITELIST
            }
            
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            self.send_error_response(f"Error scanning models: {str(e)}")
    
    def handle_image_request(self, path):
        """Serve model preview images"""
        try:
            # Extract image path from URL
            image_path = urllib.parse.unquote(path.replace('/api/image/', ''))
            full_path = os.path.join(MODEL_ROOT, image_path)
            
            print(f"🖼️ DEBUG: Image request for: {image_path}")
            print(f"🖼️ DEBUG: Full path: {full_path}")
            print(f"🖼️ DEBUG: File exists: {os.path.exists(full_path)}")
            
            if not os.path.exists(full_path):
                print(f"❌ DEBUG: Image not found: {full_path}")
                self.send_response(404)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Image not found: {image_path}".encode())
                return
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(full_path)
            if content_type is None:
                content_type = 'application/octet-stream'
            
            print(f"✅ DEBUG: Serving image: {full_path} ({content_type})")
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(os.path.getsize(full_path)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Stream the file
            with open(full_path, 'rb') as f:
                self.wfile.write(f.read())
                
        except Exception as e:
            print(f"❌ DEBUG: Error serving image: {e}")
            import traceback
            traceback.print_exc()
            self.send_error_response(f"Error serving image: {str(e)}")
    
    def handle_json_request(self, path):
        """Serve model JSON metadata"""
        try:
            # Extract JSON path from URL
            json_path = urllib.parse.unquote(path.replace('/api/json/', ''))
            full_path = os.path.join(MODEL_ROOT, json_path)
            
            if not os.path.exists(full_path):
                # Return default template
                default_template = {
                    "description": "",
                    "sd version": "",
                    "activation text": "",
                    "preferred weight": 0,
                    "negative text": "",
                    "notes": ""
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(default_template, indent=2).encode())
                return
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            with open(full_path, 'r') as f:
                self.wfile.write(f.read().encode())
                
        except Exception as e:
            self.send_error_response(f"Error serving JSON: {str(e)}")
    
    def handle_json_save(self, path):
        """Save JSON metadata for a model"""
        try:
            print(f"📝 DEBUG: Starting handle_json_save for path: {path}")
            
            # Extract JSON path from URL
            json_path = urllib.parse.unquote(path.replace('/api/json/', ''))
            print(f"📝 DEBUG: Decoded json_path: {json_path}")
            
            # Check if Content-Length header exists
            if 'Content-Length' not in self.headers:
                print(f"❌ DEBUG: No Content-Length header found")
                self.send_error_response("No Content-Length header provided")
                return
            
            # Read the content length
            content_length = int(self.headers['Content-Length'])
            print(f"📝 DEBUG: Content length: {content_length}")
            
            if content_length == 0:
                print(f"❌ DEBUG: Empty content received")
                self.send_error_response("Empty content received")
                return
            
            # Read POST data
            post_data = self.rfile.read(content_length)
            print(f"📝 DEBUG: Raw post data length: {len(post_data)}")
            print(f"📝 DEBUG: Raw post data (first 200 chars): {post_data[:200]}")
            
            # Parse JSON content
            try:
                json_content = json.loads(post_data.decode('utf-8'))
                print(f"📝 DEBUG: Saving JSON to: {json_path}")
                print(f"📝 DEBUG: JSON content: {json_content}")
            except json.JSONDecodeError as e:
                print(f"❌ DEBUG: Invalid JSON received: {e}")
                self.send_error_response(f"Invalid JSON format: {str(e)}")
                return
            except UnicodeDecodeError as e:
                print(f"❌ DEBUG: Unicode decode error: {e}")
                self.send_error_response(f"Unicode decode error: {str(e)}")
                return
            
            # Determine the full path for the JSON file
            if not json_path:
                print(f"❌ DEBUG: Empty JSON path after URL decoding")
                self.send_error_response("No JSON path provided")
                return
            
            full_path = os.path.join(MODEL_ROOT, json_path)
            print(f"📝 DEBUG: Full file path: {full_path}")
            
            # Ensure the directory exists
            dir_path = os.path.dirname(full_path)
            print(f"📝 DEBUG: Ensuring directory exists: {dir_path}")
            os.makedirs(dir_path, exist_ok=True)
            
            # Write the JSON file
            print(f"📝 DEBUG: Writing JSON file...")
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, indent=2, ensure_ascii=False)
            
            print(f"✅ DEBUG: Successfully saved JSON to: {full_path}")
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': True,
                'message': f'JSON file saved successfully to {os.path.basename(full_path)}'
            }
            
            response_data = json.dumps(response).encode()
            print(f"📝 DEBUG: Sending response: {response}")
            self.wfile.write(response_data)
            
        except Exception as e:
            print(f"❌ DEBUG: Unexpected error in handle_json_save: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.send_error_response(f"Error saving JSON: {str(e)}")
            except:
                print(f"❌ DEBUG: Failed to send error response")
                pass
    
    def handle_cache_thumbnails(self):
        """Cache thumbnails for the provided models"""
        try:
            print(f"🖼️ DEBUG: Starting handle_cache_thumbnails")
            
            # First migrate any existing thumbnails to thumbs folders
            self.migrate_existing_thumbnails()
            
            # Read the POST data to get the models
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
                models = request_data.get('models', [])
            else:
                models = []
            
            print(f"🖼️ DEBUG: Received {len(models)} models to cache thumbnails for")
            
            if not models:
                response = {
                    'success': True,
                    'message': 'No models found to cache thumbnails for.',
                    'cached_count': 0
                }
                self.send_json_response(response)
                return
            
            # Cache thumbnails — sequential, with explicit cleanup between images
            # so that even very large source previews don't pile up in RAM.
            import gc
            THUMB_MAX_DIM = 512
            cached_count = 0

            for idx, model in enumerate(models):
                preview_rel = model.get("preview")
                if not preview_rel:
                    print(f"🖼️ DEBUG: Skipping model {model.get('name', 'unknown')}: no preview")
                    continue

                # Get full paths
                preview_path = Path(MODEL_ROOT) / preview_rel

                # If preview path points to a cached thumbnail (aig_), get the original
                filename = preview_path.name
                if filename.startswith("aig_"):
                    original_filename = filename[4:]
                    original_preview_path = preview_path.parent.parent / original_filename \
                        if preview_path.parent.name == "thumbs" \
                        else preview_path.parent / original_filename
                    if original_preview_path.exists():
                        actual_source_path = original_preview_path
                        thumb_filename = filename
                    else:
                        print(f"🖼️ DEBUG: Original preview not found: {original_preview_path}")
                        continue
                else:
                    actual_source_path = preview_path
                    thumb_filename = "aig_" + filename

                if not actual_source_path.exists():
                    print(f"🖼️ DEBUG: Source path does not exist: {actual_source_path}")
                    continue

                # Always write into the thumbs/ subfolder of the *source* directory
                thumbs_dir = actual_source_path.parent / "thumbs"
                thumbs_dir.mkdir(exist_ok=True)
                thumb_path = thumbs_dir / thumb_filename

                # Force-regen: always overwrite, even if the thumbnail already exists
                try:
                    img = Image.open(actual_source_path)
                    try:
                        # draft() lets PIL decode JPEGs at reduced resolution = less RAM
                        try:
                            img.draft(img.mode, (THUMB_MAX_DIM, THUMB_MAX_DIM))
                        except Exception:
                            pass

                        # In-place thumbnail keeps memory low — only one big buffer
                        img.thumbnail((THUMB_MAX_DIM, THUMB_MAX_DIM), Image.LANCZOS)
                        img.save(thumb_path, "PNG", optimize=True)
                        cached_count += 1
                        print(f"✅ DEBUG: ({idx + 1}/{len(models)}) {thumb_path.name} ({img.size[0]}x{img.size[1]})")
                    finally:
                        img.close()
                except Exception as e:
                    print(f"❌ DEBUG: Failed to create thumbnail for {actual_source_path}: {e}")
                    continue

                # Periodically force the garbage collector so PIL's large buffers
                # are reclaimed promptly rather than waiting for the next allocation.
                if (idx + 1) % 25 == 0:
                    gc.collect()

            gc.collect()
            
            response = {
                'success': True,
                'message': f'Cached {cached_count} thumbnails in this folder.',
                'cached_count': cached_count
            }
            
            print(f"✅ DEBUG: Thumbnail caching complete. Cached {cached_count} thumbnails.")
            self.send_json_response(response)
            
        except Exception as e:
            print(f"❌ DEBUG: Error in handle_cache_thumbnails: {e}")
            import traceback
            traceback.print_exc()
            self.send_error_response(f"Error caching thumbnails: {str(e)}")
    
    def migrate_existing_thumbnails(self):
        """Migrate existing thumbnails to thumbs subfolders"""
        try:
            print(f"🔄 DEBUG: Starting thumbnail migration")
            root_path = Path(MODEL_ROOT)
            migrated_count = 0

            # Find all PNG files that might be thumbnails
            for png_file in root_path.rglob("*.png"):
                # Skip if already in thumbs folder
                if png_file.parent.name == "thumbs":
                    continue

                # ONLY migrate aig_ prefixed thumbnails
                # Source images (without aig_ prefix) should stay in parent folder for popup linking
                png_name = png_file.stem
                if not png_name.startswith("aig_"):
                    continue

                # Check if it's an aig_ thumbnail with a corresponding model file
                model_dir = png_file.parent
                base_name = png_name[4:]  # Remove "aig_" prefix
                safetensors_file = model_dir / f"{base_name}.safetensors"
                ckpt_file = model_dir / f"{base_name}.ckpt"

                # If there's a corresponding model file, migrate the thumbnail
                if safetensors_file.exists() or ckpt_file.exists():
                    thumbs_dir = model_dir / "thumbs"
                    thumbs_dir.mkdir(exist_ok=True)
                    new_path = thumbs_dir / png_file.name

                    # Move the thumbnail if it doesn't already exist in thumbs
                    if not new_path.exists():
                        png_file.rename(new_path)
                        migrated_count += 1
                        print(f"🔄 DEBUG: Migrated {png_file} -> {new_path}")

            print(f"✅ DEBUG: Migration complete. Migrated {migrated_count} thumbnails")

        except Exception as e:
            print(f"❌ DEBUG: Error during thumbnail migration: {e}")
    
    def handle_upload_thumbnail(self):
        """Handle thumbnail upload from drag and drop"""
        try:
            print(f"🖼️ DEBUG: Starting handle_upload_thumbnail")
            
            # Parse multipart form data
            import cgi
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': self.headers['Content-Type'],
                }
            )
            
            # Get uploaded file and model path
            if 'thumbnail' not in form:
                raise ValueError("No thumbnail file provided")
            
            if 'modelPath' not in form:
                raise ValueError("No model path provided")
            
            thumbnail_file = form['thumbnail']
            model_path = form['modelPath'].value
            
            print(f"🖼️ DEBUG: Uploading thumbnail for model: {model_path}")
            print(f"🖼️ DEBUG: File name: {thumbnail_file.filename}")
            print(f"🖼️ DEBUG: File type: {thumbnail_file.type}")
            
            # Validate file type
            valid_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if thumbnail_file.type not in valid_types:
                raise ValueError(f"Invalid file type: {thumbnail_file.type}")
            
            # Get model name from path
            model_name = Path(model_path).stem
            model_dir = Path(MODEL_ROOT) / Path(model_path).parent
            
            print(f"🖼️ DEBUG: Model name: {model_name}")
            print(f"🖼️ DEBUG: Model directory: {model_dir}")
            
            # Always use PNG extension for consistency
            file_ext = '.png'
            
            # Create thumbnail path
            thumbnail_filename = f"{model_name}{file_ext}"
            thumbnail_path = model_dir / thumbnail_filename
            
            print(f"🖼️ DEBUG: Saving thumbnail to: {thumbnail_path}")
            
            # Ensure directory exists
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert to PNG using PIL
            from PIL import Image
            import io
            
            # Read uploaded file data
            file_data = thumbnail_file.file.read()
            
            # Open with PIL and convert to PNG
            with Image.open(io.BytesIO(file_data)) as img:
                # Convert to RGB if necessary (for JPEG compatibility)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Keep transparency for PNG/GIF
                    img = img.convert('RGBA')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as PNG
                img.save(thumbnail_path, 'PNG')
                
                # Also create the cached thumbnail (aig_ version) in thumbs subfolder
                thumbs_dir = model_dir / "thumbs"
                thumbs_dir.mkdir(exist_ok=True)
                aig_thumbnail_filename = f"aig_{model_name}{file_ext}"
                aig_thumbnail_path = thumbs_dir / aig_thumbnail_filename
                
                print(f"🖼️ DEBUG: Creating cached thumbnail: {aig_thumbnail_path}")
                
                # Create 256px cached version
                # Calculate aspect ratio and resize uniformly
                original_width, original_height = img.size
                aspect_ratio = original_width / original_height
                
                # Scale down so longest side is 256px
                if original_width >= original_height:
                    # Width is longer
                    new_width = 256
                    new_height = int(256 / aspect_ratio)
                else:
                    # Height is longer
                    new_height = 256
                    new_width = int(256 * aspect_ratio)
                
                # Resize and save cached thumbnail
                img_cached = img.resize((new_width, new_height), Image.LANCZOS)
                img_cached.save(aig_thumbnail_path, 'PNG')
                
                print(f"✅ DEBUG: Cached thumbnail created: {aig_thumbnail_path}")
            
            print(f"✅ DEBUG: Thumbnail and cached version saved successfully")
            
            # Return relative path for the API
            relative_path = str(thumbnail_path.relative_to(Path(MODEL_ROOT)))
            
            response = {
                'success': True,
                'message': f'Thumbnail uploaded successfully for {model_name}',
                'thumbnailPath': relative_path
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            print(f"❌ DEBUG: Error in handle_upload_thumbnail: {e}")
            import traceback
            traceback.print_exc()
            self.send_error_response(f"Error uploading thumbnail: {str(e)}")
    
    def handle_open_file_explorer(self):
        """Open file explorer at the location of the specified file"""
        try:
            print(f"📁 DEBUG: Starting handle_open_file_explorer")
            
            # Read the POST data to get the file path
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
                file_path = request_data.get('filePath', '')
            else:
                file_path = ''
            
            print(f"📁 DEBUG: Received file path: {file_path}")
            
            if not file_path:
                raise ValueError("No file path provided")
            
            # Build the full path
            full_path = os.path.join(MODEL_ROOT, file_path)
            print(f"📁 DEBUG: Full path: {full_path}")
            
            # Check if file exists
            if not os.path.exists(full_path):
                raise ValueError(f"File does not exist: {full_path}")
            
            # Get the directory containing the file
            directory = os.path.dirname(full_path)
            print(f"📁 DEBUG: Directory to open: {directory}")
            
            # Open file explorer based on platform
            import platform
            import subprocess
            
            system = platform.system().lower()
            print(f"📁 DEBUG: Detected platform: {system}")
            
            if system == 'windows':
                # Windows - use explorer with /select to highlight the file
                subprocess.run(['explorer', '/select,', full_path], check=True)
            elif system == 'darwin':
                # macOS - use Finder with -R to reveal the file
                subprocess.run(['open', '-R', full_path], check=True)
            elif system == 'linux':
                # Linux - try different file managers
                try:
                    # Try xdg-open first (most universal)
                    subprocess.run(['xdg-open', directory], check=True)
                except subprocess.CalledProcessError:
                    try:
                        # Try nautilus (GNOME)
                        subprocess.run(['nautilus', directory], check=True)
                    except subprocess.CalledProcessError:
                        try:
                            # Try dolphin (KDE)
                            subprocess.run(['dolphin', directory], check=True)
                        except subprocess.CalledProcessError:
                            try:
                                # Try thunar (XFCE)
                                subprocess.run(['thunar', directory], check=True)
                            except subprocess.CalledProcessError:
                                raise RuntimeError("No supported file manager found. Please install xdg-utils, nautilus, dolphin, or thunar.")
            else:
                raise RuntimeError(f"Unsupported operating system: {system}")
            
            print(f"✅ DEBUG: Successfully opened file explorer for: {full_path}")
            
            response = {
                'success': True,
                'message': f'Opened file explorer for {os.path.basename(file_path)}'
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            print(f"❌ DEBUG: Error in handle_open_file_explorer: {e}")
            import traceback
            traceback.print_exc()
            self.send_error_response(f"Error opening file explorer: {str(e)}")
    
    def find_models_in_tree(self, tree_data, target_path):
        """Recursively find models in a specific folder using the full path"""
        if not target_path:
            return tree_data.get('_models', [])
        
        current_folder = target_path[0]
        remaining_path = target_path[1:]
        
        if current_folder in tree_data:
            if not remaining_path:  # We've reached the target folder
                return tree_data[current_folder].get('_models', [])
            elif isinstance(tree_data[current_folder], dict):
                return self.find_models_in_tree(tree_data[current_folder], remaining_path)
        
        return []  # Path not found
    
    def send_json_response(self, data):
        """Send JSON response with proper headers"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def handle_config_request(self):
        """Return server configuration"""
        config = {
            'modelRoot': MODEL_ROOT,
            'folderWhitelist': FOLDER_WHITELIST,
            'serverMode': True
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(config).encode())
    
    def handle_config_save(self):
        """Save updated server configuration"""
        global MODEL_ROOT, FOLDER_WHITELIST
        
        try:
            print(f"⚙️ DEBUG: Starting handle_config_save")
            
            # Read the POST data
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_error_response("No config data provided")
                return
            
            post_data = self.rfile.read(content_length)
            config_data = json.loads(post_data.decode('utf-8'))
            
            print(f"⚙️ DEBUG: Received config data: {config_data}")
            
            # Validate and update MODEL_ROOT
            new_model_root = config_data.get('modelRoot', '').strip()
            if new_model_root and os.path.exists(new_model_root):
                MODEL_ROOT = new_model_root
                print(f"⚙️ DEBUG: Updated MODEL_ROOT to: {MODEL_ROOT}")
            elif new_model_root:
                print(f"❌ DEBUG: Invalid MODEL_ROOT path: {new_model_root}")
                self.send_error_response(f"Model root path does not exist: {new_model_root}")
                return
            
            # Validate and update FOLDER_WHITELIST
            new_whitelist = config_data.get('folderWhitelist', [])
            if isinstance(new_whitelist, list) and all(isinstance(f, str) for f in new_whitelist):
                FOLDER_WHITELIST = [f.strip() for f in new_whitelist if f.strip()]
                print(f"⚙️ DEBUG: Updated FOLDER_WHITELIST to: {FOLDER_WHITELIST}")
            else:
                print(f"❌ DEBUG: Invalid FOLDER_WHITELIST format: {new_whitelist}")
                self.send_error_response("Folder whitelist must be an array of strings")
                return
            
            # Save configuration to file
            if save_config():
                success_message = 'Configuration updated and saved successfully'
            else:
                success_message = 'Configuration updated but failed to save to file'
            
            # Send success response
            response = {
                'success': True,
                'message': success_message,
                'config': {
                    'modelRoot': MODEL_ROOT,
                    'folderWhitelist': FOLDER_WHITELIST
                }
            }
            
            print(f"✅ DEBUG: Config updated successfully")
            self.send_json_response(response)
            
        except json.JSONDecodeError as e:
            print(f"❌ DEBUG: Invalid JSON in config save: {e}")
            self.send_error_response(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            print(f"❌ DEBUG: Error in handle_config_save: {e}")
            import traceback
            traceback.print_exc()
            self.send_error_response(f"Error saving configuration: {str(e)}")
    
    def send_error_response(self, message):
        """Send error response"""
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        error_response = {
            'success': False,
            'error': message
        }
        
        self.wfile.write(json.dumps(error_response).encode())
    
    def scan_models_hierarchically(self, root_dir):
        """
        Scan models recursively and create a hierarchical structure
        Returns a nested dictionary representing the folder structure
        (Same logic as gallery.py)
        """
        model_tree = {}
        root_path = Path(root_dir)
        
        if not root_path.exists():
            raise Exception(f"Model root directory does not exist: {root_dir}")
        
        for file_path in root_path.rglob("*"):
            # Ensure the first subfolder is in the whitelist
            if len(file_path.parts) > len(root_path.parts):
                whitelist_folder = file_path.parts[len(root_path.parts)]
                if whitelist_folder not in FOLDER_WHITELIST:
                    continue
            
            # Skip if not a model file
            if not file_path.is_file():
                continue
            
            # Check for valid model extensions
            ext_list = ['.ckpt', '.safetensors', '.pt', '.pth', '.bin']
            if file_path.suffix.lower() not in ext_list:
                continue
            
            # Break down the relative path
            relative_path = file_path.relative_to(root_path)
            
            # Ensure we start with the whitelisted folder
            current_level = model_tree
            for part in relative_path.parts[:1]:
                current_level = current_level.setdefault(part, {})
            
            # Navigate/create nested dictionary for remaining path
            for part in relative_path.parts[1:-1]:
                current_level = current_level.setdefault(part, {})
            
            # Add file details
            model_name = file_path.stem
            preview_path = file_path.parent / f"{model_name}.png"
            json_path = file_path.parent / f"{model_name}.json"
            
            # For gallery display: Check for cached thumbnail (aig_ prefix) in thumbs folder first, then fallback to main folder
            thumbs_dir = file_path.parent / "thumbs"
            cached_thumb_in_thumbs = thumbs_dir / f"aig_{model_name}.png"
            cached_thumb_legacy = file_path.parent / f"aig_{model_name}.png"
            
            if cached_thumb_in_thumbs.exists():
                preview_path = cached_thumb_in_thumbs
            elif cached_thumb_legacy.exists():
                preview_path = cached_thumb_legacy
            # Note: For popup display, we want high-res images from parent folder only
            
            # Get file modification time for sorting by date
            mod_time = file_path.stat().st_mtime
            
            # Create relative paths for API access
            preview_rel = str(preview_path.relative_to(root_path)) if preview_path.exists() else None
            json_rel = str(json_path.relative_to(root_path)) if json_path.exists() else None

            url_rel = None
            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as jf:
                        meta = json.load(jf)
                    description_text = meta.get('description') or meta.get('notes') or ''
                    if description_text:
                        m = re.search(r'(https?://[^\s)]+)', description_text)
                        if m:
                            url_rel = m.group(1).rstrip('.,;:!?)')
                except Exception:
                    pass

            current_level.setdefault('_models', []).append({
                "name": model_name,
                "path": str(relative_path),
                "preview": preview_rel,
                "json": json_rel,
                "url": url_rel,
                "modified": mod_time,
                "size": file_path.stat().st_size
            })
        
        return model_tree

def signal_handler(sig, frame):
    print('\n🛑 Server shutting down...')
    if hasattr(signal_handler, 'httpd') and signal_handler.httpd:
        try:
            signal_handler.httpd.shutdown()
        except:
            pass  # Ignore errors during shutdown
        try:
            signal_handler.httpd.server_close()
        except:
            pass  # Ignore errors during close
    sys.exit(0)

def main():
    PORT = 8001
    
    # Set up signal handler for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Change to the directory containing the HTML file
    web_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_dir)
    
    # Load configuration from file
    load_config()
    
    print(f"Model Gallery Server")
    print(f"===================")
    print(f"Model Root: {MODEL_ROOT}")
    print(f"Folder Whitelist: {', '.join(FOLDER_WHITELIST)}")
    print(f"Web Directory: {web_dir}")
    print(f"")
    
    # Check if index.html exists
    if not os.path.exists('index.html'):
        print(f"❌ ERROR: index.html not found in {web_dir}")
        print(f"Available files:")
        for f in os.listdir('.'):
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ Found index.html ({os.path.getsize('index.html')} bytes)")
    
    print(f"")
    print(f"Starting server on port {PORT}...")
    print(f"🌐 Open your browser to: http://localhost:{PORT}/")
    print(f"")
    print(f"Press Ctrl+C to stop the server")
    print(f"")
    
    with ReuseAddrTCPServer(("", PORT), ModelServerHandler) as httpd:
        # Store httpd reference for signal handler
        signal_handler.httpd = httpd
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server interrupted, shutting down...")
        finally:
            signal_handler.httpd = None

if __name__ == "__main__":
    main()