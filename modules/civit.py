import requests
import hashlib
import shutil
import os
import cv2
import json
from typing import Dict, Any
from pathlib import Path

class Civit:
    def __init__(self, base_url="https://civitai.com/api/v1/", cache_path="cache"):
        self.cache_path = cache_path
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        self.session = requests.Session()

    def _read_file(self, filename):
        try:
            with open(filename, "rb") as file:
                file.seek(0x100000)
                return file.read(0x10000)
        except FileNotFoundError:
            return b"NOFILE"
        except Exception:
            return b"NOHASH"

    def model_hash(self, filename):
        """old hash that only looks at a small part of the file and is prone to collisions"""
        file_content = self._read_file(filename)
        m = hashlib.sha256()
        m.update(file_content)
        shorthash = m.hexdigest()[0:8]
        return shorthash

#    def get_models_by_hash(self, hash):
#        url = f"{self.base_url}model-versions/by-hash/{hash}"
#        try:
#            response = requests.get(url, headers=self.headers)
#            response.raise_for_status()
#            json = response.json()
#
#            return json
#        except requests.exceptions.HTTPError as e:
#            if response.status_code == 404:
#                print("Error: Model Not Found on civit.ai")
#                return {}
#            elif response.status_code == 503:
#                print("Error: Civit.ai Service Currently Unavailable")
#                return {}
#            else:
#                print(f"HTTP Error: {e}")
#                return {}
#        except requests.exceptions.RequestException as e:
#            print(f"Error: {e}")
#            return {}

    def get_models_by_path(self, path, cache_path=None):
        data = None
        if cache_path is None:
            cache_path = Path(self.cache_path / Path(path).name)
        json_path = Path(cache_path).with_suffix(".json")

        if json_path.exists():
            try:
                with open(json_path) as f:
                    data = json.load(f)
            except:
                data = None
        if data is not None:
            return data

        hash = self.model_hash(path)
        url = f"{self.base_url}model-versions/by-hash/{hash}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                print("Error: Model Not Found on civit.ai")
            elif response.status_code == 503:
                print("Error: Civit.ai Service Currently Unavailable")
            else:
                print(f"HTTP Error: {e}")
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

        if data is None:
            return {}

        print(f"Update model data: {json_path}")
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

        return data

    def get_keywords(self, model):
        keywords = model.get("trainedWords", ["No Keywords for LoRA"])
        return keywords

    def get_model_base(self, model):
        return model.get("baseModel", "Unknown")

    def get_model_type(self, model):
        return model.get("model").get("type", "Unknown")

    def get_image(self, model, path):
        import imageio.v3 as iio

        path = path.with_suffix(".jpeg")
        image_url = None
        for preview in model.get("images", [{}]):
            url = preview.get("url")
            format = preview.get("type")
            if url:
                image_url = url
                response = self.session.get(image_url)
                response.raise_for_status()
                with open(path, "wb") as file:
                    file.write(response.content)
                if format == "video":
                    tmp_path = f"{path}.tmp"
                    os.rename(path, tmp_path)
                    video = iio.imiter(tmp_path)
                    fps = iio.immeta(tmp_path)["fps"]
                    video_out = []
                    max = 166  # Max width or height
                    for i in video:
                        oh = i.shape[0]
                        ow = i.shape[1]
                        zoom = max / oh if oh > ow else max / ow
                        out = cv2.resize(
                            i,
                            dsize=(int(ow * zoom), int(oh * zoom)),
                            interpolation=cv2.INTER_LANCZOS4,
                        )
                        video_out.append(out)
                    iio.imwrite(
                        str(path.with_suffix(".gif")), video_out, fps=fps, loop=0
                    )
                    os.remove(tmp_path)
                break
        if image_url is None:
            shutil.copyfile("html/warning.jpeg", path)
