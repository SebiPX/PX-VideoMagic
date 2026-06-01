import requests
res = requests.post('http://127.0.0.1:8002/api/render_final', data={'project_id': 'invalid', 'transcript_json': '[]', 'aiCut': False, 'subtitles': False})
print('Status Code:', res.status_code)
