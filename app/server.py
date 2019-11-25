import aiohttp
import asyncio
import uvicorn
from fastai import *
from fastai.text import *
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles

'''
datafile name and url are here
place your contruct/model name and urls here also, they are downloaded in setup_learner()
make sure that the link gives the file itself (if you click on the link it should start the download or show the raw file)
'''

data_file_url = 'https://www.dropbox.com/s/p2bqt5yrmievgts/data_lm.pkl?raw=1'
data_file_name = 'data_lm.pkl'
path = Path(__file__).parent


#start Starlette webserver, change PyTorch device to cpu to ensure no errors with Render
app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))
defaults.device = torch.device('cpu')


# Function for downloading files
async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)

# setup the AI construct
async def setup_learner():
    """
    load the model here
    i had issues loading the construct I had which is why I simply used WT103, please use a pretrained model
    """
    await download_file(data_file_url, path / data_file_name) # copy/oaste this for any file downloads you might need (construct, model etc)
    data_lm = load_data(path, file='data_lm.pkl')
    try:
        learn = language_model_learner(data_lm, AWD_LSTM, pretrained=URLs.WT103, drop_mult=0.5)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise

# function to start initialising the learner, server does not run until this is complete
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
    # get the text from POST request
    req = await request.form()
    TEXT = req['entered-text']
    # you may want to add input for N_WORDS and N_SENTENCES - for the latter remember to use list comprehension
    N_WORDS = 300
    N_SENTENCES = 1
    # mess around with the temperature a bit - you may get better results
    prediction = "\n" + learn.predict(TEXT, n_words = N_WORDS, temperature = 0.75)
    return JSONResponse({'result': str(prediction)})


if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="debug")

