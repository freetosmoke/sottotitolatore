import re
import json

def verify_dom_integrity(orig_content, new_content):
    orig_scripts = re.findall(r'<script(?:\s+[^>]*)?>(.*?)</script>', orig_content, re.DOTALL)
    orig_js = '\n'.join(orig_scripts)
    
    # Trova tutti i getElementById dal JS originale
    required_ids = set(re.findall(r'getElementById\([\"\']([^\"\']+)[\"\']\)', orig_js))
    
    # Trova gli ID nel nuovo file
    new_html = re.sub(r'<script(?:\s+[^>]*)?>.*?</script>', '', new_content, flags=re.DOTALL)
    new_ids = set(re.findall(r'\bid=[\"\']([^\"\']+)[\"\']', new_html))
    
    missing = required_ids - new_ids
    print(f"Total required JS IDs: {len(required_ids)}")
    print(f"Total new HTML IDs: {len(new_ids)}")
    if missing:
        print(f"WARNING! Missing {len(missing)} IDs in new HTML:")
        for m in sorted(missing):
            print(f"  - {m}")
        return False
    else:
        print("PERFECT! All required JS IDs are present in the new HTML.")
        return True

if __name__ == '__main__':
    import subprocess, sys
    
    new_path = sys.argv[2] if len(sys.argv) > 2 else 'web_static/index.html'
    with open(new_path, 'r', encoding='utf-8') as f:
        new_content = f.read()
        
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            orig_content = f.read()
    else:
        res = subprocess.run(
            ['git', 'show', 'UI_BASELINE_BEFORE_SUB_STUDIO_REDESIGN:web_static/index.html'],
            capture_output=True, text=True
        )
        orig_content = res.stdout

    verify_dom_integrity(orig_content, new_content)

