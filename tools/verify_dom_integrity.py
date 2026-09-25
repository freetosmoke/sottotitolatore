import re
import json

def verify_integrity(original_path, new_path):
    with open(original_path, 'r', encoding='utf-8') as f:
        orig = f.read()
    with open(new_path, 'r', encoding='utf-8') as f:
        new = f.read()

    orig_scripts = re.findall(r'<script(?:\s+[^>]*)?>(.*?)</script>', orig, re.DOTALL)
    orig_js = '\n'.join(orig_scripts)
    
    # Trova tutti i getElementById dal JS originale
    required_ids = set(re.findall(r'getElementById\([\"\']([^\"\']+)[\"\']\)', orig_js))
    
    # Trova gli ID nel nuovo file
    new_html = re.sub(r'<script(?:\s+[^>]*)?>.*?</script>', '', new, flags=re.DOTALL)
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
    import sys
    orig = sys.argv[1] if len(sys.argv) > 1 else 'backup_ui_pre_redesign_20260925/web_static/index.html'
    new = sys.argv[2] if len(sys.argv) > 2 else 'web_static/index.html'
    verify_integrity(orig, new)
