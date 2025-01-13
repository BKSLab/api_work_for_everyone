from http import HTTPStatus

import uvicorn

from fastapi import FastAPI
from fastapi.responses import JSONResponse


app = FastAPI()


@app.get(path='/api/regions', tags=['Список регионов'])
async def get_regions_list():
    """Обрабатывает GET запрос на получение списка регионов."""
    return JSONResponse(
        content={
           'id': 1,
           'region_name': 'Республика Адыгея (Адыгея)',
           'region_code_tv': '01',
           'region_code_hh': '1422'
        },
        status_code=HTTPStatus.OK
    )


if __name__ == '__main__':
    uvicorn.run(
        app='main:app',
        reload=True,
        host='0.0.0.0',
        port=8000
    )

#  python api_service\main.py