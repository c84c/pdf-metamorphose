import io
import logging
import tempfile
import zipfile
from typing import Annotated, Literal

import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from pdf2image import convert_from_bytes
from starlette.responses import RedirectResponse

logger = logging.getLogger(__file__)

app = FastAPI()


@app.post("/pdf/metamorphose")
def create_upload_file(
    pdf_file: Annotated[UploadFile, File(description="A file read as UploadFile")],
    format: Literal["jpeg", "jpg", "png"] = "jpeg"
):
    # controls on request content
    if pdf_file.content_type != "application/pdf":
        raise HTTPException(400, detail="Invalid document type: only PDF file accepted")

    # helper to manipulate arguments
    image_fmt = format
    if format == "jpg":
        image_fmt = "jpeg"

    # I don't know other options then zip to return multiple files
    zip_buffer = io.BytesIO()
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # convert pdf to image
            with tempfile.TemporaryDirectory() as path:
                images = convert_from_bytes(
                    pdf_file.file.read(),
                    fmt=format,
                    output_folder=path,
                    output_file="page",
                    dpi=350,
                    thread_count=4
                )

                # insert each generated image in ZIP archive
                for (i, image) in enumerate(images):
                    # https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.tobytes
                    # say to use save() with a BytesIO object
                    with io.BytesIO() as im_buffer:
                        image.save(im_buffer, format=image_fmt)
                        # create zip file
                        zip_info = zipfile.ZipInfo(f"page{i + 1}.{image_fmt}")
                        zip_file.writestr(zip_info, im_buffer.getvalue())

        # reset zip file
        zip_buffer.seek(0)
        headers = {"Content-Disposition": "attachment; filename=images.zip"}
        return Response(zip_buffer.getvalue(), headers=headers, media_type="application/zip")

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=400, detail='There was an error processing the data')

    finally:
        zip_buffer.close()


@app.get("/")
def root():
    return RedirectResponse("/docs")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
