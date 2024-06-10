import flwr as fl
import tensorflow as tf
from tensorflow import keras
import sys
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Auxiliary methods
def getDist(y):
    y_flat = y.flatten()  # Ensure y is a flat array
    print("Class distribution:", np.bincount(y_flat))
    
    
    # Use matplotlib to plot the class distribution
    class_counts = np.bincount(y_flat)
    plt.bar(range(len(class_counts)), class_counts)
    plt.title("Count of data classes")
    plt.xlabel("Class")
    plt.ylabel("Count")
    plt.show()

def getData(dist, x, y):
    dx = []
    dy = []
    counts = [0 for i in range(10)]
    for i in range(len(x)):
        if counts[y[i]] < dist[y[i]]:
            dx.append(x[i])
            dy.append(y[i])
            counts[y[i]] += 1
    return np.array(dx), np.array(dy)

# Load and compile Keras model
model = keras.Sequential([
    keras.layers.Flatten(input_shape=(28, 28)),
    keras.layers.Dense(128, activation='relu'),
    keras.layers.Dense(256, activation='relu'),
    keras.layers.Dense(10, activation='softmax')
])
model.compile("adam", "sparse_categorical_crossentropy", metrics=["accuracy"])

# Load dataset
(x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
x_train, x_test = x_train[..., np.newaxis] / 255.0, x_test[..., np.newaxis] / 255.0
dist = [10, 10, 10, 10, 10, 10, 50000, 50000, 10, 10]
x_train, y_train = getData(dist, x_train, y_train)
getDist(y_train)

# Define Flower client
class FlowerClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return model.get_weights()

    def fit(self, parameters, config):
        model.set_weights(parameters)
        r = model.fit(x_train, y_train, epochs=1, validation_data=(x_test, y_test), verbose=0)
        hist = r.history
        print("Fit history : ", hist)
        return model.get_weights(), len(x_train), {}

    def evaluate(self, parameters, config):
        model.set_weights(parameters)
        loss, accuracy = model.evaluate(x_test, y_test, verbose=0)
        print("Eval accuracy : ", accuracy)
        return loss, len(x_test), {"accuracy": accuracy}

# Ensure command-line argument is provided
if len(sys.argv) < 2:
    print("Usage: python client3.py <PORT>")
    sys.exit(1)

# Start Flower client
fl.client.start_client(
    server_address="localhost:" + str(sys.argv[1]),
    client=FlowerClient().to_client(),
    grpc_max_message_length=1024*1024*1024
)
