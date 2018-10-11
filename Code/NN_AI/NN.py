import tensorflow as tf
import tensorflow.contrib.slim as slim
import numpy as np
import matplotlib.pyplot as plt
import sys,os
sys.path.append(os.path.realpath(".."))
sys.path.append(os.path.realpath("../Structs"))
sys.path.append(os.path.realpath("../DB"))
from CC_Agent import CC_Agent
from Blackjack import Hand
from NN_Move import NN_Move
from Moves import Moves
from Trainer import Init_Trainer
from Trainer import Batch_Trainer
from datetime import datetime

"""
    - defines classes for both the primary netowrk and the target network
    - also defines the behaviour for the NN agent
"""

# class for the primary network
class Q_Net():
    def __init__(self, input_size, hidden_size, output_size, rnn_cell, myScope, training=True):
        self.init_feed_forward(input_size, hidden_size, output_size, myScope)
        self.rnn_processing(rnn_cell, hidden_size, myScope)
        self.split_streams(hidden_size, output_size)
        self.predict()
        self.gen_loss(output_size)
        self.train_update()

        if not training:
            self.disable_dropout()

    # dropout layers should be disabled when training is complete
    def disable_dropout(self):
        for dropout in self.dropout_layers:
            dropout.is_Training = False

    def rnn_processing(self, rnn_cell, hidden_size, myScope):
        # Take the output from the final fully connected layer and send it to a recurrent layer.
        # The input must be reshaped into [batch x trace x units] for rnn processing,
        # and then returned to [batch x units] when sent through the upper levles.
        self.trainLength = tf.placeholder(dtype=tf.int32)
        self.batch_size = tf.placeholder(dtype=tf.int32, shape=[])
        output_flat = tf.reshape(self.final_hidden, [self.batch_size, self.trainLength, hidden_size])
        self.state_in = rnn_cell.zero_state(self.batch_size, tf.float32)
        self.rnn, self.rnn_state = tf.nn.dynamic_rnn(
            inputs=output_flat, cell=rnn_cell, dtype=tf.float32, initial_state=self.state_in, scope=myScope + '_rnn')
        self.rnn = tf.reshape(self.rnn, shape=[-1, hidden_size])

    def init_feed_forward(self, inp_size, hidden_size, output_size, myScope):
        # Establish feed-forward part of the network
        self.input_layer = tf.placeholder(shape=[None, inp_size], dtype=tf.float32)

        hidden_layer1 = slim.fully_connected(self.input_layer, hidden_size,
                                             biases_initializer=None,
                                             activation_fn=tf.nn.relu,
                                             scope=(myScope+"_hidden1"))  # Rectified linear activation func.

        dropout1 = slim.dropout(hidden_layer1, scope=myScope+"_dropout1")

        hidden_layer2 = slim.fully_connected(dropout1, hidden_size,
                                             biases_initializer=None,
                                             activation_fn=tf.nn.relu,
                                             scope=(myScope+"_hidden2"))

        dropout2 = slim.dropout(hidden_layer2, scope=myScope+"_dropout2")

        self.final_hidden = slim.fully_connected(dropout2, hidden_size,
                                                 activation_fn=tf.nn.relu,
                                                 biases_initializer=None,
                                                 scope=(myScope+"_final_hidden"))  # Softmax activation func. -> changed to relu, as no longer output

        self.dropout_layers = [dropout1, dropout2]

        #self.action = tf.argmax(self.output_layer, 1)

    def split_streams(self, hidden_size, output_size):
        # The output from the recurrent player is then split into separate Value and Advantage streams
        self.streamA, self.streamV = tf.split(self.rnn, 2, 1)
        self.AW = tf.Variable(tf.random_normal([hidden_size // 2, output_size]))
        self.VW = tf.Variable(tf.random_normal([hidden_size // 2, 1]))
        self.Advantage = tf.matmul(self.streamA, self.AW)
        self.Value = tf.matmul(self.streamV, self.VW)
        self.salience = tf.gradients(self.Advantage, self.input_layer)

    def predict(self):
         # Combine streams for final prediction value
        self.Qout = self.Value + tf.subtract(self.Advantage, tf.reduce_mean(self.Advantage, axis=1, keep_dims=True))
        self.predict = tf.argmax(self.Qout, 1)

    def gen_loss(self, output_size):
        # Loss calculated by taking the sum of squares difference between the target and prediction Q values.
        self.targetQ = tf.placeholder(shape=[None], dtype=tf.float32)
        self.actions = tf.placeholder(shape=[None], dtype=tf.int32)
        self.actions_onehot = tf.one_hot(self.actions, output_size, dtype=tf.float32)

        self.Q = tf.reduce_sum(tf.multiply(self.Qout, self.actions_onehot), axis=1)

        self.td_error = tf.square(self.targetQ - self.Q)

        # In order to only propogate accurate gradients through the network, we will mask the first
        # half of the losses for each trace as per Lample & Chatlot 2016
        self.maskA = tf.zeros([self.batch_size, self.trainLength // 2])
        self.maskB = tf.ones([self.batch_size, self.trainLength // 2])
        self.mask = tf.concat([self.maskA, self.maskB], 1)
        self.mask = tf.reshape(self.mask, [-1])
        self.loss = tf.reduce_mean(self.td_error * self.mask)

    # update the network by using Adam optimizer algorithm
    def train_update(self):
        self.trainer = tf.train.AdamOptimizer(learning_rate=0.0001)
        self.updateModel = self.trainer.minimize(self.loss)

# target network is essentially the same as the primary network, but needs
# a few extra behaviours defined to sync it back with the primary network when required
class Target_Net(Q_Net):
    def __init__(self, input_size, hidden_size, output_size, rnn_cell, myScope, training=True):
        super().__init__(input_size, hidden_size, output_size, rnn_cell, myScope, training)
        self.ops = None

    #These functions update the parameters of our target network with those of the primary network.
    def updateTargetGraph(self, tfVars, tau):
        total_vars = len(tfVars)
        op_holder = []
        for idx,var in enumerate(tfVars[0:total_vars//2]):
            op_holder.append(tfVars[idx+total_vars//2].assign((var.value()*tau) + ((1-tau)*tfVars[idx+total_vars//2].value())))
        self.ops = op_holder
        return op_holder

    def updateTarget(self, sess):
        op_holder = self.ops
        for op in op_holder:
            sess.run(op)
        total_vars = len(tf.trainable_variables())
        a = tf.trainable_variables()[0].eval(session=sess)
        b = tf.trainable_variables()[total_vars//2].eval(session=sess)
        if a.all() != b.all():
            print("Target Set Failed")


# Class for NN agent
class NN(CC_Agent):
    def __init__(self, setting="default", hand=None, restore_type="default", Training=True, auto_load=True):
        super().__init__(ID="nn", extra_type=["nn"])
        self.rnn_state = None
        self.sess = None

        self.parameters = self.set_parameters(setting=setting)
        self.train_params = self.set_training_params(setting=setting)

        if hand is None:
            self.Hand = Hand(self.ID)

        self.initalise_NN(Training)
        self.start_session()

        if auto_load:
            self.load_model(restore_type)

    # sets the bevhiour parameters of the nn
    def set_parameters(self, setting="default"):
        if setting is "default":
            #Setting the training parameters
            nn_params = {
                "gamma": .99,  # Discount factor on the target Q-values
                "start_epsilon" : 1, #Starting chance of random action
                "epsilon" : 1, # tracking value for epsilon - MAKE THIS AN ATTRIBUTE?
                "end_epsilon" : 0.001, #Final chance of random action
                "path_default" : "./nn_data", #The path to save our model to.
                "hidden_size" : 32, #The size of the final convolutional layer before splitting it into Advantage and Value streams.
                "no_features" : 6, # How many features to input into the network
                "no_actions" : 2, # No actions the network can take
                "summaryLength" : 100, #Number of epidoes to periodically save for analysis -- not applicable?
                "annealing_steps": 1000,  # How many steps of training to reduce startE to endE.
                "tau" : 0.001,
                "policy" : "e-greedy",
                "hand_val_norm_const": 1 / 30,  # value to normalise hand values by
                "batch_size": 8,  # How many experience traces to use for each training step.
                "trace_length": 2,  # How long each experience trace will be when training
            }

            start_epsilon = nn_params["start_epsilon"]
            end_epsilon = nn_params["end_epsilon"]
            annealing_steps = nn_params["annealing_steps"]


            # Set the rate of random action decrease.
            nn_params["epsilon"] = start_epsilon
            nn_params["epsilon_step"] = (start_epsilon - end_epsilon) / annealing_steps

        return nn_params

    # sets parameters used in intial training
    def set_training_params(self, setting="default"):
        if setting == "default":
            train_params = {
                "batch_size": 8,  # How many experience traces to use for each training step.
                "trace_length": 2,  # How long each experience trace will be when training
                "update_freq": 2,  # How often to perform a training step.
                "train_steps": 20000,  # How many episodes of game environment to train network with.
                "explore_steps": 1000,  # how many steps for initial explore, before training
                "save_model_frequency": 50,  # how often to save the model
                "update_frequency": 5,  # how often to update the network weights
                "test_steps": 20000,  # how many iterations to test
                "hand_val_norm_const": 1 / 30  # value to normalise hand values by
            }

            rewards = {
                "winReward": 3,
                "lossCost": -3,
                "bustCost": 0,
                "hand_value_discount": 1 / 2
            }
        return train_params


    # sets up both the primary and target rnn
    # initialises tf and sets the target net equal to primary net
    def initalise_NN(self, Training=True):
        no_features = self.parameters["no_features"]
        hidden_size = self.parameters["hidden_size"]
        no_actions = self.parameters["no_actions"]
        tau = self.parameters["tau"]

        tf.reset_default_graph()
        Primary_rnn_cell = tf.contrib.rnn.BasicLSTMCell(num_units=hidden_size, state_is_tuple=True)
        Target_rnn_cell = tf.contrib.rnn.BasicLSTMCell(num_units=hidden_size, state_is_tuple=True)
        self.Primary_Network = Q_Net(no_features, hidden_size, no_actions, Primary_rnn_cell, 'main', Training)
        self.Target_Network = Target_Net(no_features, hidden_size, no_actions, Target_rnn_cell, 'target', Training)
        self.rnn_state = np.zeros([1, hidden_size]), np.zeros([1, hidden_size])

        self.init = tf.global_variables_initializer()
        trainables = tf.trainable_variables()
        self.targetOps = self.Target_Network.updateTargetGraph(trainables, tau)
        # saver is used for saving and restoring the nn model (the weights)
        self.saver = tf.train.Saver() # max_to_keep=5

    # resets the rnn_state
    def rnn_state_reset(self):
        hidden_size = self.parameters["hidden_size"]
        self.rnn_state = np.zeros([1, hidden_size]), np.zeros([1, hidden_size])

    # gets the new rnn_state
    def rnn_state_update(self, game_state):
        self.rnn_state = self.sess.run(self.Primary_Network.rnn_state,
                                      feed_dict={
                                          self.Primary_Network.input_layer: [game_state],
                                          self.Primary_Network.trainLength: 1,
                                          self.Primary_Network.state_in: self.rnn_state,
                                          self.Primary_Network.batch_size: 1}
                                      )
        return self.rnn_state

    # start the session, run the assigned training type
    def init_training(self, type="group_all"):
        # no context manager so that session does not have to be restarted every time a new move is needed
        trainer = Init_Trainer(self, training_params=self.train_params, training_type=type)
        self.start_session()
        self.sess.run(self.init)
        trainer.train(self.sess)
        self.stop_session()

    # runs trainer for new games NN has played in
    # does not update if there are not more than 50 games ot update from
    # ADD TO NEA WU
    def update_training(self):
        trainer = Batch_Trainer(self, training_params=self.train_params)
        no_games = trainer.get_num_games_to_train()
        if no_games >= 50:
            self.start_session()
            self.sess.run(self.init)

            trainer.train_new_games()
            print("success")
        return no_games

    # Override from CC_Agent
    # exploring relates to the inital part of training when the agent is exploring the environment and takes random actions
    def get_move(self, all_players, exploring=False):
        game_state = self.get_state(all_players)
        chances = self.get_chances(game_state)

        # simple check so the neural network always takes the dominant strategy.
        if chances["bust"] == 1:
            return Moves.STAND
        elif chances["bust"] == 0:
            return Moves.HIT
        else:
            move_next = self.getNextAction(chances, game_state, exploring=exploring)
            return move_next

    # returns the next move of the agent
    # side effect => updated rnn cell state after every move
    def getNextAction(self, chances, game_state, exploring=False):
        # pass through NN model, and get the next move
        game_state = self.get_features(chances, game_state)
        move = NN_Move.choose_action(self.parameters, self.Primary_Network, game_state, self.rnn_state, self.sess,
                                     exploring=exploring)
        self.rnn_state_update(game_state)
        if move == True:
            move = Moves.HIT
        elif move == False:
            move = Moves.STAND
        return move

    # gets the features which wil be used as the parameter for the input layer of the nn
    # [normalise_agent_hand_val, normalised_best_val, chances] TODO update this so that it includes win margin
    def get_features(self, chances, game_state):
        hand_val_norm_const = self.parameters["hand_val_norm_const"]
        features = []
        # append the hand values of agent hand and best player hand to the features array
        # should always be [agent_hand, best_player_hand]
        for hand in game_state:
            if isinstance(hand, int):
                hand_val = hand
            else:
                hand_val = hand.get_value()
            hand_val_normalised = hand_val * hand_val_norm_const
            features.append(hand_val_normalised)
        for key in sorted(chances):
            features.append(chances[key])
        return features

    # init the tf session - MUST BE CALLED BEFORE ANY TF ACTION OCCURS
    def start_session(self):
        self.sess = tf.Session()

    # stops the tf session - CALL WHEN TF WORK IS COMPLETED
    def stop_session(self):
        if self.sess is not None:
            self.sess.close()
            self.sess = None

    # checkpoints the current model for later use
    # model based-parameterisation
    # save a new model for a new paramaterisation
    def save_model(self):
        path = self.parameters["path_default"]
        # Make a path for our model to be saved in.
        if not os.path.exists(path):
            os.makedirs(path)
        # eg. 28-02-2018,15-30-10
        model_version = datetime.now().strftime("%d-%m-%Y,%H-%M-%S")
        model_type = "/model-default-"
        #(path + model_type + model_version + ".cptk")
        self.saver.save(self.sess, "nn_data/model.cptk")

    # loads the last checkpointed model - session must have been started before model loading
    # TODO IMPLEMENT THE RESTORATION OF DIFFERENT FILES
    def load_model(self, restore_type="default"):
        path = self.parameters["path_default"]
        ckpt = tf.train.get_checkpoint_state(path) # gets the checkpoint from the last checkpoint file
        #self.saver.restore(self.sess, ckpt.model_checkpoint_path)
        self.saver.restore(self.sess, "NN_AI/nn_data/model.cptk") #NN_AI/nn_data/model.cptk
        print("model loaded successfully")

    # updates the target and the primary network - should be called after game steps reaches its train frequency
    # exp buffer - experience_buffer class used to store game samples in training
    def update_networks(self, exp_buffer):
        batch_size = self.parameters["batch_size"]
        hidden_size = self.parameters["hidden_size"]
        trace_length = self.parameters["trace_length"]
        y = self.parameters["gamma"]

        self.Target_Network.updateTarget(self.sess)
        rnn_state_update = (np.zeros([batch_size, hidden_size]), np.zeros([batch_size, hidden_size])) # using intial rnn state for training
        trainBatch = exp_buffer.sample(batch_size, trace_length)  # Get a random batch of experiences.

        # Below we perform the Double-DQN update to the target Q-values
        primary_out = self.sess.run(self.Primary_Network.predict, feed_dict={
            self.Primary_Network.input_layer: np.vstack(trainBatch[:, 3]),
            self.Primary_Network.trainLength: trace_length,
            self.Primary_Network.state_in: rnn_state_update,
            self.Primary_Network.batch_size: batch_size
        })

        target_out = self.sess.run(self.Target_Network.Qout, feed_dict={
            self.Target_Network.input_layer: np.vstack(trainBatch[:, 3]),
            self.Target_Network.trainLength: trace_length,
            self.Target_Network.state_in: rnn_state_update,
            self.Target_Network.batch_size: batch_size
        })

        end_multiplier = -(trainBatch[:, 4] - 1)
        doubleQ = target_out[range(batch_size * trace_length), primary_out]
        targetQ = trainBatch[:, 2] + (y * doubleQ * end_multiplier)
        # Update the network with our target values.
        self.sess.run(self.Primary_Network.updateModel,
                      feed_dict={
                          self.Primary_Network.input_layer: np.vstack(trainBatch[:, 0]),
                          self.Primary_Network.targetQ: targetQ,
                          self.Primary_Network.actions: trainBatch[:, 1],
                          self.Primary_Network.trainLength: trace_length,
                          self.Primary_Network.state_in: rnn_state_update,
                          self.Primary_Network.batch_size: batch_size}
                      )

    # at the end of each game each hand is passed and the card counter is decremented
    def update_end_game(self, new_cards):
        self.decrement_CC(new_cards)
        self.rnn_state_reset()

    # returns all the values and the names of the trainable variables loaded in the current tf graph
    def get_trainable_vars(self):
        if self.sess is None:
            self.start_session()
        trainables = tf.trainable_variables()
        names = [v.name for v in trainables]
        v = [self.sess.run(v) for v in trainables]

        toReturn = zip(names, v)

        self.stop_session()
        return toReturn

if __name__ == "__main__":
    nn = NN()
    #nn.init_training()
    nn.start_session()
    nn.sess.run(nn.init)
    nn.update_training()
    nn.stop_session()
