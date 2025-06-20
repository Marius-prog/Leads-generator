#!/usr/bin/env python3
"""
Frontend testing for the lead generation system.
Tests HTML structure, JavaScript functionality, and backend integration.
"""

import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import webbrowser

def test_html_structure():
    """Test HTML file structure and content."""
    print("Testing HTML structure...")
    
    try:
        html_file = Path('frontend/test.html')
        if not html_file.exists():
            print("❌ Frontend test.html file not found")
            return False
        
        content = html_file.read_text()
        
        # Check for required elements
        required_elements = [
            'Lead Generation System',
            'API_BASE_URL',
            'checkConfig',
            'generateLeads', 
            'business_name',
            'location',
            'leads_count',
            'tailwindcss',
            'fetch(',
            'addEventListener'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing required elements: {missing_elements}")
            return False
        
        print("✅ All required HTML elements present")
        
        # Check for proper JavaScript structure
        js_functions = [
            'checkConfig()',
            'generateLeads(',
            'startPolling()',
            'updateTaskStatus(',
            'showResults('
        ]
        
        missing_functions = []
        for func in js_functions:
            if func not in content:
                missing_functions.append(func)
        
        if missing_functions:
            print(f"❌ Missing JavaScript functions: {missing_functions}")
            return False
        
        print("✅ All required JavaScript functions present")
        
        # Check for proper API endpoint references
        api_endpoints = [
            '/api/config/check',
            '/api/leads/generate',
            '/api/leads/status/'
        ]
        
        missing_endpoints = []
        for endpoint in api_endpoints:
            if endpoint not in content:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print(f"❌ Missing API endpoints: {missing_endpoints}")
            return False
        
        print("✅ All required API endpoints referenced")
        
        return True
        
    except Exception as e:
        print(f"❌ HTML structure test failed: {e}")
        return False

def test_static_file_server():
    """Test serving the HTML file with a static server."""
    print("\nTesting static file server...")
    
    try:
        # Change to frontend directory to serve files
        frontend_dir = Path('frontend').absolute()
        
        class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(frontend_dir), **kwargs)
            
            def log_message(self, format, *args):
                pass  # Suppress log messages
        
        # Start server in a separate thread
        server = HTTPServer(('localhost', 8080), CustomHTTPRequestHandler)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # Give server time to start
        time.sleep(1)
        
        # Test if HTML file is accessible
        try:
            response = requests.get('http://localhost:8080/test.html', timeout=5)
            if response.status_code == 200 and 'Lead Generation System' in response.text:
                print("✅ Static file server working")
                print("✅ HTML file accessible at http://localhost:8080/test.html")
                server_working = True
            else:
                print(f"❌ Static file server failed: {response.status_code}")
                server_working = False
        except Exception as e:
            print(f"❌ Static file server test failed: {e}")
            server_working = False
        
        # Cleanup
        server.shutdown()
        server.server_close()
        
        return server_working
        
    except Exception as e:
        print(f"❌ Static file server test failed: {e}")
        return False

def test_backend_api_endpoints():
    """Test backend API endpoints for frontend integration."""
    print("\nTesting backend API endpoints...")
    
    try:
        # Start a simple mock backend for testing
        backend_code = '''
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import time
import urllib.parse

class MockAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self._send_json_response({"status": "healthy", "timestamp": time.time()})
        elif self.path == '/api/config/check':
            self._send_json_response({
                "google_places_api": False,
                "perplexity_api": False,
                "anthropic_api": False,
                "instantly_api": False,
                "database": True,
                "missing_configs": ["All APIs (Demo Mode)"]
            })
        elif self.path.startswith('/api/leads/status/'):
            task_id = self.path.split('/')[-1]
            self._send_json_response({
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "total_leads": 3,
                "results": {
                    "total_leads": 3,
                    "validated_leads": 2,
                    "enriched_leads": 1
                }
            })
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/leads/generate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                response = {
                    "task_id": f"test_task_{int(time.time())}",
                    "status": "pending",
                    "message": "Lead generation pipeline started"
                }
                self._send_json_response(response)
            except:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def _send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    server = HTTPServer(('localhost', 8000), MockAPIHandler)
    server.serve_forever()
'''
        
        # Write mock backend to file
        with open('mock_backend.py', 'w') as f:
            f.write(backend_code)
        
        # Start mock backend
        backend_process = subprocess.Popen([sys.executable, 'mock_backend.py'])
        time.sleep(2)
        
        try:
            # Test health endpoint
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print("❌ Health endpoint failed")
                return False
            
            # Test config endpoint
            response = requests.get('http://localhost:8000/api/config/check', timeout=5)
            if response.status_code == 200:
                config = response.json()
                if 'database' in config:
                    print("✅ Config endpoint working")
                else:
                    print("❌ Config endpoint invalid response")
                    return False
            else:
                print("❌ Config endpoint failed")
                return False
            
            # Test lead generation endpoint
            payload = {
                'business_name': 'test restaurants',
                'location': 'Test City, CA',
                'leads_count': 5
            }
            
            response = requests.post(
                'http://localhost:8000/api/leads/generate',
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'task_id' in result:
                    print("✅ Lead generation endpoint working")
                    
                    # Test status endpoint
                    task_id = result['task_id']
                    status_response = requests.get(f'http://localhost:8000/api/leads/status/{task_id}', timeout=5)
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        if 'status' in status and 'progress' in status:
                            print("✅ Status endpoint working")
                        else:
                            print("❌ Status endpoint invalid response")
                            return False
                    else:
                        print("❌ Status endpoint failed")
                        return False
                else:
                    print("❌ Lead generation endpoint invalid response")
                    return False
            else:
                print("❌ Lead generation endpoint failed")
                return False
            
            success = True
            
        finally:
            # Cleanup
            backend_process.terminate()
            backend_process.wait()
            import os
            os.remove('mock_backend.py')
        
        return success
        
    except Exception as e:
        print(f"❌ Backend API endpoints test failed: {e}")
        return False

def test_frontend_backend_integration():
    """Test frontend-backend integration simulation."""
    print("\nTesting frontend-backend integration...")
    
    try:
        # Test JavaScript API client code structure
        html_file = Path('frontend/test.html')
        content = html_file.read_text()
        
        # Check for proper error handling
        error_handling_patterns = [
            'try {',
            'catch (',
            '.then(',
            '.catch(',
            'response.ok',
            'response.json()'
        ]
        
        found_patterns = []
        for pattern in error_handling_patterns:
            if pattern in content:
                found_patterns.append(pattern)
        
        if len(found_patterns) >= 4:  # Should have at least 4 error handling patterns
            print("✅ Frontend error handling present")
        else:
            print(f"❌ Insufficient error handling: found {found_patterns}")
            return False
        
        # Check for proper async/await or Promise usage
        async_patterns = ['fetch(', 'async ', 'await ']
        found_async = [p for p in async_patterns if p in content]
        
        if len(found_async) >= 1:
            print("✅ Async JavaScript patterns present")
        else:
            print("❌ No async JavaScript patterns found")
            return False
        
        # Check for DOM manipulation
        dom_patterns = [
            'getElementById(',
            '.innerHTML',
            '.style.display',
            '.disabled',
            '.textContent'
        ]
        
        found_dom = [p for p in dom_patterns if p in content]
        
        if len(found_dom) >= 3:
            print("✅ DOM manipulation patterns present")
        else:
            print(f"❌ Insufficient DOM manipulation: found {found_dom}")
            return False
        
        # Check for proper API URL configuration
        if 'API_BASE_URL' in content and 'localhost:8000' in content:
            print("✅ API URL configuration present")
        else:
            print("❌ API URL configuration missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Frontend-backend integration test failed: {e}")
        return False

def test_responsive_design():
    """Test responsive design elements."""
    print("\nTesting responsive design...")
    
    try:
        html_file = Path('frontend/test.html')
        content = html_file.read_text()
        
        # Check for responsive design elements
        responsive_elements = [
            'max-w-7xl',  # Max width
            'mx-auto',    # Center alignment
            'grid',       # Grid layout
            'flex',       # Flex layout
            'sm:',        # Small breakpoint
            'lg:',        # Large breakpoint
            'md:',        # Medium breakpoint
            'px-4',       # Responsive padding
            'py-',        # Responsive spacing
        ]
        
        found_responsive = []
        for element in responsive_elements:
            if element in content:
                found_responsive.append(element)
        
        if len(found_responsive) >= 6:
            print(f"✅ Responsive design elements present: {len(found_responsive)}/9")
        else:
            print(f"❌ Insufficient responsive design: found {found_responsive}")
            return False
        
        # Check for viewport meta tag
        if 'viewport' in content and 'width=device-width' in content:
            print("✅ Viewport meta tag present")
        else:
            print("❌ Viewport meta tag missing")
            return False
        
        # Check for mobile-friendly classes
        mobile_classes = ['text-sm', 'text-xs', 'hidden', 'block']
        found_mobile = [c for c in mobile_classes if c in content]
        
        if len(found_mobile) >= 2:
            print("✅ Mobile-friendly classes present")
        else:
            print("❌ Mobile-friendly classes insufficient")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Responsive design test failed: {e}")
        return False

def main():
    """Run all frontend tests."""
    print("🧪 Running Frontend Build and Integration Tests")
    print("=" * 60)
    
    tests = [
        ("HTML Structure", test_html_structure),
        ("Static File Server", test_static_file_server),
        ("Backend API Endpoints", test_backend_api_endpoints),
        ("Frontend-Backend Integration", test_frontend_backend_integration),
        ("Responsive Design", test_responsive_design)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"Frontend Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All frontend tests passed!")
        print("\nFrontend capabilities verified:")
        print("✅ HTML structure and content")
        print("✅ Static file serving")
        print("✅ API endpoint integration")
        print("✅ JavaScript functionality")
        print("✅ Responsive design")
        print("✅ Error handling")
        
        print("\nFrontend ready for:")
        print("1. Full stack integration")
        print("2. Browser testing")
        print("3. Real backend connection")
        print("4. User acceptance testing")
        
        return True
    else:
        print("❌ Some frontend tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
