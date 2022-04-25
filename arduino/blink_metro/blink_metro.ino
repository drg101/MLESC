#include <TensorFlowLite.h>

#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"
#include "contextual_model.h"

tflite::MicroErrorReporter micro_error_reporter;
tflite::ErrorReporter* error_reporter = &micro_error_reporter;

const tflite::Model* model = ::tflite::GetModel(contextual_model_tflite);

tflite::AllOpsResolver resolver;

uint8_t tensor_arena[2916];

tflite::MicroInterpreter interpreter(model, resolver, tensor_arena,
                                     2916, error_reporter);


// the setup function runs once when you press reset or power the board
void setup() {
  // initialize digital pin 13 as an output.
  Serial.begin(9600); // begin Serial communication
  pinMode(13, OUTPUT);

  if (model->version() != TFLITE_SCHEMA_VERSION) {
  TF_LITE_REPORT_ERROR(error_reporter,
      "Model provided is schema version %d not equal "
      "to supported version %d.\n",
      model->version(), TFLITE_SCHEMA_VERSION);
  }

  interpreter.AllocateTensors();
}

// the loop function runs over and over again forever
void loop() {
//  digitalWrite(13, HIGH);   // turn the LED on (HIGH is the voltage level)
//  delay(200);              // wait for a second
//  digitalWrite(13, LOW);    // turn the LED off by making the voltage LOW
//  delay(200);              // wait for a second
  long int t1 = millis();
  TfLiteTensor* input = interpreter.input(0);
  input->data.f[0] = 0.5;
  input->data.f[1] = 0;
  input->data.f[2] = 1;


  TfLiteStatus invoke_status = interpreter.Invoke();
  if (invoke_status != kTfLiteOk) {
    TF_LITE_REPORT_ERROR(error_reporter, "Invoke failed\n");
    Serial.println("invoke fail");
  }

  TfLiteTensor* output = interpreter.output(0);
  float value = output->data.f[0];
  
  long int t2 = millis();
  Serial.print("Time taken by the task: "); Serial.print(t2-t1); Serial.println(" milliseconds");
  Serial.print(value); // print text
  Serial.print("\n"); // print a new line
}
