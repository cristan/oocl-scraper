from pathlib import Path

import onnxruntime as ort
from PIL import Image
import numpy as np

model_path = Path(__file__).resolve().parent / 'weights' / 'oocl.onnx'


class ONNXModel:
    def __init__(self):
        """
        Initialize the ONNX model by loading it once.

        Args:
        - model_path (str): Path to the ONNX model file.
        """
        self.model_path = model_path
        self.session = ort.InferenceSession(model_path)
        self.input_name = self.session.get_inputs()[0].name

    def infer(self, input_data):
        """
        Perform inference on the input data.

        Args:
        - input_data (numpy.ndarray): The input data to pass to the model.

        Returns:
        - output (numpy.ndarray): The output of the model inference.
        """
        if not isinstance(input_data, np.ndarray):
            input_data = np.array(input_data)
        outputs = self.session.run(None, {self.input_name: input_data})
        return not np.argmax(outputs[0][0]) and np.max(outputs[0][0]) > 0.9

    @staticmethod
    def preprocess_image(image, target_size=(64, 64)):
        """
        Load and preprocess the image to match the model's input requirements.

        Args:
        - image_path (Image): Pil image.
        - target_size (tuple): The target size to which the image will be resized.

        Returns:
        - processed_image (numpy.ndarray): Preprocessed image ready for model input.
        """
        image = image.resize(target_size)
        image_array = np.array(image).astype(np.float32)    # noqa
        image_array = np.transpose(image_array, (2, 0, 1))
        image_array /= 255.0
        image_array = np.expand_dims(image_array, axis=0)
        return image_array


if __name__ == "__main__":
    onnx_model = ONNXModel()
    input_data = onnx_model.load_and_preprocess_image('true2.png')

    for i in range(5):
        output = onnx_model.infer(input_data)
        print(f"Inference {i + 1} result:", output)
