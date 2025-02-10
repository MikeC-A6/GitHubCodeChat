import fnmatch
import re
from typing import List, Dict, Any

# Define patterns to ignore
IGNORE_PATTERNS = [
    # Git files
    '.git/**', '.gitignore', '.gitattributes', '.gitmodules',
    
    # Python
    '*.pyc', '*.pyo', '*.pyd', '__pycache__', '.pytest_cache',
    '.coverage', '.tox', '.nox', '.mypy_cache', '.ruff_cache',
    '.hypothesis', 'venv', '.venv', 'env', '.env', 'virtualenv',
    'site-packages', '*.egg-info', '*.egg', '*.whl',
    
    # Node/JavaScript
    'node_modules/**', 'bower_components', 'package-lock.json',
    'yarn.lock', '.npm', '.yarn', '.pnpm-store', '*.min.js',
    '*.min.css', '*.map', '.eslintcache',
    
    # Java
    '*.class', '*.jar', '*.war', '*.ear', '*.nar', 'target/',
    '.gradle/', 'build/', '.settings/', '.project', '.classpath',
    'gradle-app.setting', '*.gradle',
    
    # C/C++
    '*.o', '*.obj', '*.so', '*.dll', '*.dylib', '*.exe', '*.lib',
    '*.out', '*.a', '*.pdb',
    
    # Xcode/iOS
    '.build/', '*.xcodeproj/', '*.xcworkspace/', '*.pbxuser',
    '*.mode1v3', '*.mode2v3', '*.perspectivev3', '*.xcuserstate',
    'xcuserdata/', '.swiftpm/',
    
    # Ruby
    '*.gem', '.bundle/', 'vendor/bundle', 'Gemfile.lock',
    '.ruby-version', '.ruby-gemset', '.rvmrc',
    
    # Rust
    'Cargo.lock', '**/*.rs.bk',
    
    # .NET
    'bin/', 'pkg/', 'obj/', '*.suo', '*.user', '*.userosscache',
    '*.sln.docstates', 'packages/', '*.nupkg',
    
    # Version Control
    '.svn', '.hg',
    
    # Media files
    '*.svg', '*.png', '*.jpg', '*.jpeg', '*.gif', '*.ico', '*.pdf',
    '*.mov', '*.mp4', '*.mp3', '*.wav', '*.webp', '*.ttf',
    
    # IDE/Editor
    '.idea', '.vscode', '.vs', '*.swp', '*.swo', '*.swn',
    '.settings', '*.sublime-*',
    
    # Logs and temp files
    '*.log', '*.bak', '*.tmp', '*.temp', '.cache', '.sass-cache',
    
    # OS specific
    '.DS_Store', 'Thumbs.db', 'desktop.ini',
    
    # Build directories
    'build', 'dist', 'target', 'out',
    
    # Documentation
    '.docusaurus', '.next', '.nuxt',
    
    # Infrastructure
    '.terraform', '*.tfstate*',
    
    # Dependencies
    'vendor/', 'poetry.lock', 'Pipfile.lock',
    
    # Other
    '*.html', '*.yml',
    'tools/typespec-go/node_modules/**'
]

def should_ignore_file(file_path: str) -> bool:
    """
    Check if a file should be ignored based on the ignore patterns.
    
    Args:
        file_path: Path of the file to check
        
    Returns:
        bool: True if file should be ignored, False otherwise
    """
    # Convert file path to use forward slashes for consistency
    file_path = file_path.replace('\\', '/')
    
    for pattern in IGNORE_PATTERNS:
        # Convert glob pattern to regex pattern
        regex_pattern = fnmatch.translate(pattern)
        if re.match(regex_pattern, file_path):
            return True
            
        # Also check if pattern matches anywhere in the path
        if '/**' in pattern:
            base_pattern = pattern.replace('/**', '')
            if base_pattern and base_pattern in file_path:
                return True
    
    return False

def filter_repository_files(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out files that should be ignored from the repository files list.
    
    Args:
        files: List of file dictionaries with 'name' and 'content' keys
        
    Returns:
        List[Dict[str, Any]]: Filtered list of files
    """
    return [
        file for file in files 
        if not should_ignore_file(file['name'])
    ] 