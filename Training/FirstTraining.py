from imageai.Prediction.Custom import ModelTraining
import tensorflow as tf

config = tf.ConfigProto()
config.gpu_options.allow_growth = True
sess = tf.Session(config=config)

model_trainer = ModelTraining()
model_trainer.setModelTypeAsResNet()
model_trainer.setDataDirectory("idenprof")
model_trainer.trainModel(num_objects=3, num_experiments=200, enhance_data=True, batch_size=3, show_network_summary=True)
