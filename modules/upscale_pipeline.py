import os
import traceback
import numpy as np
import torch
import modules.async_worker as worker
from modules.settings import default_settings
from shared import path_manager
import comfy.utils
from comfy_extras.chainner_models import model_loading
from comfy_extras.nodes_upscale_model import ImageUpscaleWithModel
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

class pipeline:
    pipeline_type = ["template"]

    model_hash = ""

    def load_upscaler_model(self, model_name):
        model_path = path_manager.get_file_path(
            model_name,
            default = os.path.join(path_manager.model_paths["upscaler_path"], model_name)
        )
        sd = comfy.utils.load_torch_file(str(model_path), safe_load=True)
        if "module.layers.0.residual_group.blocks.0.norm1.weight" in sd:
            sd = comfy.utils.state_dict_prefix_replace(sd, {"module.": ""})
        out = model_loading.load_state_dict(sd).eval()
        return out

    def load_base_model(self, name):
        # Check if model is already loaded
        if self.model_hash == name:
            return
        print(f"Loading model: {name}")
        self.model_hash = name
        return

    def load_keywords(self, lora):
        filename = lora.replace(".safetensors", ".txt")
        try:
            with open(filename, "r") as file:
                data = file.read()
            return data
        except FileNotFoundError:
            return " "

    def load_loras(self, loras):
        return

    def refresh_controlnet(self, name=None):
        return

    def clean_prompt_cond_caches(self):
        return

    def process(
        self,
        positive_prompt,
        negative_prompt,
        input_image,
        controlnet,
        main_view,
        steps,
        width,
        height,
        image_seed,
        start_step,
        denoise,
        cfg,
        sampler_name,
        scheduler,
        clip_skip,
        callback,
        gen_data=None,
    ):
    

        input_image = input_image.convert("RGB")
        input_image = np.array(input_image).astype(np.float32) / 255.0
        input_image = torch.from_numpy(input_image)[None,]

        upscaler_name = controlnet["upscaler"]
        worker.outputs.append(["preview", (-1, f"Load upscaling model {upscaler_name}...", None)])
        print(f"Upscale: Loading model {upscaler_name}")
        upscale_path = path_manager.get_file_path(upscaler_name)
        if upscale_path == None:
            upscale_path = path_manager.get_file_path("4x-UltraSharp.pth")

        try:
            upscaler_model = self.load_upscaler_model(upscale_path)

            worker.outputs.append(["preview", (-1, f"Upscaling image ...", None)])
            decoded_latent = ImageUpscaleWithModel().upscale(
                upscaler_model, input_image
            )[0]

            worker.outputs.append(["preview", (-1, f"Converting ...", None)])
            images = [
                np.clip(255.0 * y.cpu().numpy(), 0, 255).astype(np.uint8)
                for y in decoded_latent
            ]
            worker.outputs.append(["preview", (-1, f"Done ...", None)])
        except:
            traceback.print_exc()
            worker.outputs.append(["preview", (-1, f"Oops ...", "error.png")])
            images =  []

        return images
