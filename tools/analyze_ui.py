import re
import json

def analyze():
    with open('web_static/index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Separa script e markup
    scripts = re.findall(r'<script(?:\s+[^>]*)?>(.*?)</script>', content, re.DOTALL)
    all_js = "\n".join(scripts)
    
    html_without_scripts = re.sub(r'<script(?:\s+[^>]*)?>.*?</script>', '', content, flags=re.DOTALL)

    html_ids = set(re.findall(r'\bid=[\"\']([^\"\']+)[\"\']', html_without_scripts))
    get_elem_ids = set(re.findall(r'getElementById\([\"\']([^\"\']+)[\"\']\)', all_js))
    qs_ids = set(re.findall(r'querySelector(?:All)?\([\"\']#([a-zA-Z0-9_\-]+)', all_js))
    
    all_js_ids = get_elem_ids | qs_ids
    
    print(f"Total HTML IDs in markup: {len(html_ids)}")
    print(f"Total IDs accessed by JS: {len(all_js_ids)}")
    
    # Trova le funzioni globali JS
    func_defs = re.findall(r'(?:function\s+([a-zA-Z0-9_$]+)\s*\(|const\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|let\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|var\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)', all_js)
    functions = set()
    for match in func_defs:
        for name in match:
            if name:
                functions.add(name)
    print(f"Total JS functions defined: {len(functions)}")

    # Trova tutti gli onclick, onchange, etc. nel markup
    event_attrs = re.findall(r'\bon([a-z]+)=[\"\']([^\"\']+)[\"\']', html_without_scripts)
    print(f"Total inline event handlers in HTML: {len(event_attrs)}")
    
    # Trova addEventListener in JS
    event_listeners = re.findall(r'addEventListener\([\"\']([^\"\']+)[\"\']', all_js)
    print(f"Total addEventListener calls in JS: {len(event_listeners)}")

    # Endpoints
    fetches = set(re.findall(r'fetch\([\"\'`](/[^\"\'`?\$]+)', all_js))
    print(f"Total fetch endpoints: {len(fetches)}")
    
    # Write report
    report = {
        "html_ids": sorted(list(html_ids)),
        "js_ids": sorted(list(all_js_ids)),
        "functions_count": len(functions),
        "sample_functions": sorted(list(functions))[:50],
        "fetch_endpoints": sorted(list(fetches)),
        "inline_events_sample": event_attrs[:20]
    }
    with open('tools/ui_analysis_report.json', 'w', encoding='utf-8') as out:
        json.dump(report, out, indent=2)
    print("Report written to tools/ui_analysis_report.json")

if __name__ == '__main__':
    analyze()
