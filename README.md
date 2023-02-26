# manga crawler

A test crawler of manga, developing

# Quick start
```shell
pip install -r requirements.txt  
python main.py
```

# Api
  
## Search

### Request

`GET /api/dogemanga/search`  
`curl -i -H 'Accept: application/json' -d 'manga_name=电锯人' http://localhost:5000`

### Response

`{data: object, code: number}`

## Confirm Selection

### Request

`Post /api/dogemanga/confirm`  
`curl -i -H 'Accept: application/json' -d 'manga_object= {'manga_name': string, 'manga_id': string, 'artist_name': string, 'thumbnail': string}' http://localhost:5000`

### Response

`{data: 'submitted', code: number}`

## Get Manga Lirbrary

### Request

`Post /api/dogemanga/lib`  
`curl -i -H 'Accept: application/json' -d '' http://localhost:5000`

### Response

`{data: Object array, code: number}`