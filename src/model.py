import time
import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten, Conv2D, MaxPooling2D, Conv1D
from .feature import get_all_features

def make_generator_model() -> tf.keras.models.Model:
    return


def make_discriminator_model() -> tf.keras.models.Model:
    num_fc = 512

    # ... other parts of the GAN
    a = tf.constant([1.0, -0.5, 3.4, -2.1, 0.0, -6.5], dtype=tf.float32)
    cnn_net = Sequential()
    cnn_net.add(Conv1D(32, kernel_size=5, strides=2))
    cnn_net.add(Activation(tf.nn.leaky_relu(a, alpha=0.01)))
    cnn_net.add(Conv1D(64, kernel_size=5, strides=2))
    cnn_net.add(tf.nn.leaky_relu(alpha=0.01))
    cnn_net.add(tf.layers.batch_normalization())
    cnn_net.add(Conv1D(128, kernel_size=5, strides=2))
    cnn_net.add(tf.nn.leaky_relu(alpha=0.01))
    cnn_net.add(tf.layers.batch_normalization())

    # Add the two Fully Connected layers
    cnn_net.add(tf.layers.dense(220, use_bias=False), tf.layers.batch_normalization(), tf.nn.leaky_relu(alpha=0.01))
    cnn_net.add(tf.layers.dense(220, use_bias=False), Activation('relu'))
    cnn_net.add(tf.layers.Dense(1))

    print(cnn_net)
    return


class GAN:
    def __init__(self, generator, discriminator):
        self.generator = generator
        self.discriminator = discriminator
        self.cross_entropy = tf.keras.losses.BinaryCrossentropy(from_logits=True)
        self.generator_optimizer = tf.keras.optimizers.Adam(1e-4)
        self.discriminator_optimizer = tf.keras.optimizers.Adam(1e-4)
        self.batch_size = 32
        self.noise_dim = 100
        checkpoint_dir = '../training_checkpoints'
        self.checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt")
        self.checkpoint = tf.train.Checkpoint(generator_optimizer=self.generator_optimizer,
                                              discriminator_optimizer=self.discriminator_optimizer,
                                              generator=self.generator,
                                              discriminator=self.discriminator)

    def discriminator_loss(self, real_output, fake_output):
        real_loss = self.cross_entropy(tf.ones_like(real_output), real_output)
        fake_loss = self.cross_entropy(tf.zeros_like(fake_output), fake_output)
        total_loss = real_loss + fake_loss
        return total_loss

    def generator_loss(self, fake_output):
        return self.cross_entropy(tf.ones_like(fake_output), fake_output)

    @tf.function
    def train_step(self, data):
        noise = tf.random.normal([self.batch_size, self.noise_dim])

        with tf.GradientTape() as gen_tape, tf.GradientTape() as disc_tape:
            generated_data = self.generator(noise, training=True)

            real_output = self.discriminator(data, training=True)
            fake_output = self.discriminator(generated_data, training=True)

            gen_loss = self.generator_loss(fake_output)
            disc_loss = self.discriminator_loss(real_output, fake_output)

        gradients_of_generator = gen_tape.gradient(gen_loss, self.generator.trainable_variables)
        gradients_of_discriminator = disc_tape.gradient(disc_loss, self.discriminator.trainable_variables)

        self.generator_optimizer.apply_gradients(zip(gradients_of_generator, self.generator.trainable_variables))
        self.discriminator_optimizer.apply_gradients(
            zip(gradients_of_discriminator, self.discriminator.trainable_variables))

    def train(self, dataset, epochs):
        for epoch in range(epochs):
            start = time.time()

            for data in dataset:
                self.train_step(data)

            # Save the model every 15 epochs
            if (epoch + 1) % 15 == 0:
                self.checkpoint.save(file_prefix=self.checkpoint_prefix)

            print('Time for epoch {} is {} sec'.format(epoch + 1, time.time() - start))


if __name__ == '__main__':
    df = pd.read_pickle("../data/prices/AAPL.pkl")
    df = get_all_features(df)
    train_df, test_df = df[:int(df.shape[0])], df[int(df.shape[0]):]
    generator = make_generator_model()
    discriminator = make_discriminator_model()
    gan = GAN(generator, discriminator)
    gan.train(train_df, 1000)






