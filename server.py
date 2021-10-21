import os
import shutil
from fastapi import FastAPI,Request, UploadFile, File,BackgroundTasks
from fastapi.templating import Jinja2Templates
import ocr
import uuid
app = FastAPI()

templates = Jinja2Templates(directory='templates')

@app.get('/')
def home(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.post('/extract_text')
async def perform_ocr(image: UploadFile = File(...)): #(...)-> ellipsis(a dt in python , just a placeholder.)
    temp_file = _save_file_to_disk(image, path='temp', save_as='temp')
    text = await ocr.read_image(temp_file)
    return {'filename': image.filename, 'text': text}

def _save_file_to_disk(uploaded_file, path='.', save_as='default'):
    extension = os.path.splitext(uploaded_file.filename)[-1] #catch the extension of the uploaded file
    print(extension)
    temp_file = os.path.join(path,save_as+extension) #.samename.extension
    print(temp_file)
    with open(temp_file,'wb') as buffer: # empty file is opened for writing in binary mode
        shutil.copyfileobj(uploaded_file.file, buffer)
    return temp_file

@app.post('/bulk_extract_text')
async def bulk_perform_ocr(request: Request, bg_task:BackgroundTasks):
    images = await request.form()

    folder_name = str(uuid.uuid4())
    os.mkdir(folder_name)

    for image in images.values():
        temp_file = _save_file_to_disk(image, path= folder_name, save_as=image.filename)

    bg_task.add_task(ocr.read_images_from_dir, folder_name, write_to_file=True)
    return {'task_id': folder_name, 'num_files': len(images)}

@app.post('/bulk_output/{task_id}')
async def bulk_output(task_id):
    text_map = {}
    for file_ in os.listdir(task_id):
        if file_.endswith("txt"):
            text_map[file_] = open(os.path.join(task_id, file_)).read()
    return {'task_id': task_id, 'output': text_map}