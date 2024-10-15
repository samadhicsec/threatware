import uvicorn
from actions.handler import lambda_handler, getVersion
from fastapi import FastAPI, Response

app = FastAPI()

def apicall(lang: str = None, format: str = None, action: str = None, scheme: str = None, docloc: str = None, meta: str = None, doctemplate: str = None, ID: str = None, IDprefix: str = None, reports: str = None):

    if format not in ['json', 'yaml', 'html']:
        format = 'json'

    if meta not in ['none', 'tags', 'properties']:
        meta = "tags"

    if reports not in ['none', 'assets', 'controls', 'all']:
        reports = "none"

    # Build input for handler
    event ={}

    class Object(object):
        pass
    context = Object()
    # setattr(context, "threatware.cli", False)
    setattr(context, "threatware.api", True)

    event["queryStringParameters"] = {}
    event["queryStringParameters"]["lang"] = lang
    event["queryStringParameters"]["format"] = format
    event["queryStringParameters"]["action"] = action
    event["queryStringParameters"]["scheme"] = scheme
    event["queryStringParameters"]["docloc"] = docloc
    event["queryStringParameters"]["meta"] = meta
    event["queryStringParameters"]["doctemplate"] = doctemplate
    event["queryStringParameters"]["ID"] = ID
    event["queryStringParameters"]["IDprefix"] = IDprefix
    event["queryStringParameters"]["reports"] = reports

    response = lambda_handler(event, context)

    return Response(content=response["body"], headers=response["headers"], status_code=response["statusCode"])

@app.get("/")
@app.get("/version/")
def version():

    return getVersion('threatware')

@app.get("/convert/")
def convert(scheme: str, docloc: str, lang: str = None, format: str = None, meta: str = None):
    action = "convert"

    return apicall(lang=lang, format=format, action=action, scheme=scheme, docloc=docloc, meta=meta)

@app.get("/verify/")
def verify(scheme: str, docloc: str, doctemplate: str, reports:str = None, lang: str = None, format: str = None, meta: str = None):
    action = "verify"

    return apicall(lang=lang, format=format, action=action, scheme=scheme, docloc=docloc, doctemplate=doctemplate, meta=meta)

@app.get("/manage/indexdata")
def manage_indexdata(ID: str, lang: str = None, format: str = None, meta: str = None):
    action = "manage.indexdata"

    return apicall(lang=lang, format=format, action=action, ID=ID, meta=meta)

@app.get("/manage/create")
def manage_create(IDprefix: str, scheme: str, docloc: str, lang: str = None, format: str = None, meta: str = None):
    action = "manage.create"

    return apicall(lang=lang, format=format, action=action, IDprefix=IDprefix, scheme=scheme, docloc=docloc, meta=meta)

@app.get("/manage/check")
def manage_check(scheme: str, docloc: str, lang: str = None, format: str = None, meta: str = None):
    action = "manage.check"

    return apicall(lang=lang, format=format, action=action, scheme=scheme, docloc=docloc, meta=meta)

@app.get("/manage/submit")
def manage_submit(scheme: str, docloc: str, lang: str = None, format: str = None, meta: str = None):
    action = "manage.submit"

    return apicall(lang=lang, format=format, action=action, scheme=scheme, docloc=docloc, meta=meta)

@app.get("/measure/")
def measure(scheme: str, docloc: str, doctemplate: str, lang: str = None, format: str = None, meta: str = None):
    action = "measure"

    return apicall(lang=lang, format=format, action=action, scheme=scheme, docloc=docloc, doctemplate=doctemplate, meta=meta)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)