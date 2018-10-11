import numpy as np
import sys,os
sys.path.append(os.path.realpath(".."))

"""
    - static class which defines different exploration strategies for the NN
"""

class NN_Move:
    @staticmethod
    def choose_action(parameters, Primary_Network, game_state, rnn_state, sess, exploring=False):
        policy = parameters["policy"]
        if policy == "e-greedy":
            move = NN_Move.choose_action_e_greedy(parameters, Primary_Network, game_state, rnn_state, sess, exploring=exploring)
            return move

    # e-greedy policy => choose highest value action, with chance e of picking a random action
    # epsilon starts high during training and is decremented over time
    @staticmethod
    def choose_action_e_greedy(parameters, Primary_Network, game_state, rnn_state, sess, exploring):
        e = parameters["epsilon"]

        # random exploration if explore stage or prob is less than epsilon
        if np.random.rand(1) < e or exploring:
            end_range = parameters["no_actions"]
            a = np.random.randint(0, end_range)
        else:
            a, new_rnn_state = sess.run([Primary_Network.predict, Primary_Network.rnn_state],
                                    feed_dict={
                                        Primary_Network.input_layer: [game_state],
                                        Primary_Network.trainLength: 1,
                                        Primary_Network.state_in: rnn_state,
                                        Primary_Network.batch_size: 1}
                                    )
            a = a[0]

        # decrement epsilon
        if not exploring:
            if parameters["epsilon"] > parameters["end_epsilon"]:
                parameters["epsilon"] -= parameters["epsilon_step"]

        return a
