import aiohttp
import asyncio
import uvicorn
from fastai import *
from fastai.vision import *
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from torch import nn as nn
export_file_url = 'https://www.dropbox.com/s/6bgq8t6yextloqp/export.pkl?raw=1'
export_file_name = 'fine_tuned_enc.pth'

path = Path(__file__).parent
export_file_url = "https://www.dropbox.com/s/apu0seqcmuy6rpp/fine_tuned_enc.pth?dl=1"

class TempModel(nn.Module):
    def __init__(self):
        super(TempModel, self).__init__() # Initialize self._modules as OrderedDict
        self.conv1 = nn.Conv2d(1, 20, 5)     # Add key conv1 to self._modules
        self.conv2 = nn.Conv2d(20, 20, 5)    # Add key conv2 to self._modules 
    def forward(self, inp):
        return self.conv1(inp)


app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))
defaults.device = 'cpu'
async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)

async def setup_learner():
    await download_file(export_file_url, path / export_file_name)
    try:
        learn = TempModel()
        learn.load_state_dict(torch.load(path / export_file_name))
        learn.eval()
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    req = await request.form()
    TEXT = req['entered-text']
    N_WORDS = 100
    N_SENTENCES = 1
    prediction = TEXT + "\n".join(learn.predict(TEXT, N_WORDS, temperature=1) for _ in range(N_SENTENCES))
    return JSONResponse({'result': prediction})


if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="debug")

