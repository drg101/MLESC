import tflite_runtime.interpreter as tflite
import numpy as np

interpreter = tflite.Interpreter('../../analyze/contextual_model.tflite')
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

inp = np.array([[0.44857768043523677,-0.008362388883404969,0.66]], dtype='float32')
interpreter.set_tensor(input_details[0]['index'], inp)
interpreter.invoke()
res = interpreter.get_tensor(output_details[0]['index'])[0][0]

print(res)