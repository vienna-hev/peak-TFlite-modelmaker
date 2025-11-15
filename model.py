spec = model_spec.get('efficientdet_lite0')

train_data, validation_data, test_data = object_detector.DataLoader.from_csv('gs://cloud-ml-data/img/openimage/csv/salads_ml_use.csv')

model = object_detector.create(train_data, model_spec=spec, batch_size=8, train_whole_model=True, validation_data=validation_data)

model.evaluate(test_data)

model.export(export_dir='take68\workspace\exported_model')

model.evaluate_tflite('model.tflite', test_data)
