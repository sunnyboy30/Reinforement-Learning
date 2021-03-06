import tensorflow as tf
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
import torch
from torch.optim import Adam
import gym
import math
from save_as_gif import save_frames_as_gif 
import pdb #Set a breakpoint with pdb.set_trace()



class Q_net(nn.Module):
    """This is the class for the basic neural net class
    It is used to create the neural net that tries to learn the Q-function
    The layers can probably be improved, it is just very vanila
    """
    def __init__(self, input_dim, output_dim):
        super(Q_net, self).__init__()
        self.l1 = nn.Linear(input_dim, 255)
        self.l2 = nn.Linear(255, 120)
        self.l3 = nn.Linear(120, output_dim)


    def forward(self, x):
        x = F.relu(self.l1(x))
        x = F.relu(self.l2(x))
        return F.relu(self.l3(x))

class Buffer():
    """
    This is used to save state transistion sets
    """
    def __init__(self):
        #Implement this for experience replay
        self.states = []
        self.next_states = []
        self.actions = []
        self.rewards = []
        self.dones = []


    def store(self, state, next_state, action, reward,done):
        self.states.append(state)
        self.next_states.append(next_state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.dones.append(done)

    def get(self):
        """Returns a dictionary containing the data with the necessary datatype dtype=torch.float32"""
        data = dict(states=self.states, next_states=self.next_states, actions=self.actions, rewards=self.rewards, dones=self.dones)
        return {k: torch.as_tensor(v, dtype=torch.float32) for k,v in data.items()}

    def clear(self):
        self.states = []
        self.next_states = []
        self.actions = []
        self.rewards = []
        self.done = []

class DQN_agent():
    """Creates an an agent consisting of two neural nets (old and new Q function) that can interact with an environment"""
    def __init__(self):
        """Initialize learning parameters"""
        self.input_dim = 4 #State space dimension
        self.output_dim = 2 #Number of actions
        self.e_greedy = 1
        self.e_min = 0.01
        self.e_decay = 0.999
        self.epochs = 50
        self.steps_per_epoch = 3000
        self.gamma = 0.999
        self.learning_rate = 1e-3
        self.target_update = 10
        self.q_net = Q_net(self.input_dim, self.output_dim)
        self.q_net_target = Q_net(self.input_dim, self.output_dim)

    @torch.no_grad()
    def choose_action(self, state, env):
        """Choose action greedily given the Q function"""
        state = torch.as_tensor(state, dtype = torch.float32)
        if np.random.random() < self.e_greedy:
            return env.action_space.sample()
        else:
            return np.argmax(self.q_net(state).detach().numpy())

    @torch.no_grad()
    def choose_action_perform(self, state, env):
        """Choose action greedily given the Q function during perfomance (no e_greedy i.e no random actions)"""
        state = torch.as_tensor(state, dtype = torch.float32)
        return np.argmax(self.q_net(state).detach().numpy())

    def train(self):
        """Train the net describing the Q function"""
        env = gym.make('CartPole-v0')
        state = env.reset()
        buffer = Buffer()

        optimizer = Adam(self.q_net.parameters(), lr=self.learning_rate)
        episode_reward = 0
        average_rew = 0
        i_episode = 0
        finished = False
        while not finished:
            episode_reward = 0
            done = False
            while not done:
                action = self.choose_action(state, env)
                next_state, reward, done, _ = env.step(action)
                episode_reward += reward
                #env.render()
                buffer.store(state, next_state, action, reward, done)
                state = next_state

            data = buffer.get()
            buffer.clear()
            env.reset()

            future_reward = self.q_net_target(data['next_states'])
            q_next_state = torch.max(future_reward, axis = 1)[0]
            q_next_state[-1] = 0
            target = data['rewards'] + self.gamma*q_next_state
            #In the next line the Q-values corresponding to the choses action are calculated
            Q = self.q_net(data['states'])[range(self.q_net(data['states']).shape[0]) , data['actions'].long()]
            loss = torch.sum((target - Q)**2)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            #Decay of e to move from exploration to exploitation
            if self.e_greedy > self.e_min:
                self.e_greedy *= self.e_decay

            i_episode += 1
            #Update the neural net used for the old Q-values
            if i_episode % self.target_update == 0:
                self.q_net_target.load_state_dict(self.q_net.state_dict())

            #Show some stats
            average_rew += episode_reward
            if i_episode % 100 == 0:
                mean = average_rew/100
                print(mean)
                #print(self.e_greedy)
                average_rew = 0
                if mean > 197:
                    finished = True

    def perform(self):
        """Perfom based on the trained net"""
        env = gym.make('CartPole-v0')
        state = env.reset()
        frames = []
        for _ in range(3):
            done = False
            while not done:
                action = self.choose_action_perform(state, env)
                next_state, reward, done, _ = env.step(action)
                env.render()
                frames.append(env.render(mode="rgb_array"))
                state = next_state

            env.reset()
        save_frames_as_gif(frames)
        env.close()
            


# agent = DQN_agent()
# agent.train()
# agent.perform()


