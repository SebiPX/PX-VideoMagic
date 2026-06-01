import requests
res = requests.post('http://127.0.0.1:8001/api/render_final', data={'project_id': 'invalid', 'transcript_json': '[]', 'aiCut': False, 'subtitles': False})
print('Status Code:', res.status_code)
try:
    print('JSON:', res.json())
except Exception as e:
    print('Error decoding JSON:', e)
    print('Text:', res.text)
