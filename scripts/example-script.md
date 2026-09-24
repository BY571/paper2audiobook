---
title: Proximal Policy Optimization Algorithms
authors: John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, Oleg Klimov
year: 2017
source: https://arxiv.org/abs/1707.06347
---

## Opening

This is Proximal Policy Optimization Algorithms, by John Schulman and colleagues at OpenAI, published as a preprint in 2017. It is a methods paper. It introduces a new family of policy gradient algorithms for reinforcement learning, known today simply as PPO, and it has since become one of the most widely used algorithms in the field.

## The problem

In reinforcement learning an agent learns a policy, which is a rule for choosing actions, by interacting with an environment and collecting rewards. When the policy is a neural network, there were three main families of methods in 2017. Deep Q-learning, which worked well on Atari games but had not been shown to work on continuous control problems and was poorly understood. Vanilla policy gradient methods, which are simple but waste a lot of data and are fragile. And trust region policy optimization, or TRPO, which was data efficient and reliable but complicated to implement.

The authors' complaint about TRPO is specific. TRPO keeps each policy update small by solving a constrained optimization problem with second-order machinery. That machinery does not play well with architectures that share parameters between the policy and the value function, with dropout, or with auxiliary tasks. It is also awkward to scale to large models and parallel implementations.

The underlying issue is this. Policy gradient methods get their gradient estimate from a batch of data collected by the current policy. It would be very appealing to reuse each batch for several optimization steps, because collecting data is expensive. But if you take several gradient steps on the plain policy gradient objective using the same batch, the policy drifts far from the one that collected the data, the estimate becomes invalid, and training collapses. So most methods take one step per batch and throw the data away. The paper wants a method that can safely take many steps per batch, matches TRPO's reliability, and needs nothing more than ordinary first-order gradient descent.

## The idea in one breath

Instead of constraining how far the policy may move, change the objective so that the policy has no incentive to move too far. The authors clip the term that measures how much the new policy's action probability has changed relative to the old one, and take the pessimistic side of the clipped and unclipped versions. The result is a lower bound on the true objective. The policy is rewarded for improving up to a point and gets nothing for going beyond it. That single change lets you run several epochs of minibatch gradient descent on the same data.

## Where it sits

TRPO is the direct ancestor. It maximizes a surrogate objective, essentially the advantage-weighted ratio of new to old action probabilities, subject to a hard constraint on how much the policy distribution may change, measured by an average KL divergence. Solving that constrained problem needs conjugate gradient and line search, which is where the implementation complexity comes from. The theory behind TRPO actually suggests using a penalty instead of a hard constraint, but in practice a single penalty coefficient does not work across problems, or even within one problem as training progresses. That is why TRPO went with the constraint.

The other relevant baselines are advantage actor critic, or A2C, the synchronous version of the well known A3C algorithm, and ACER, an actor critic with experience replay that is sample efficient on Atari but considerably more complex. Vanilla policy gradient and the cross entropy method appear as weaker baselines for continuous control.

PPO sits between vanilla policy gradient and TRPO. It keeps the simplicity of the former, a few lines of change to a standard implementation, and gets most of the stability of the latter. The paper also proposes a second variant, an adaptive KL penalty that raises or lowers the penalty coefficient after each update to hit a target divergence. The authors include it mainly as a baseline, because it performed worse than clipping in their experiments.

## How it works

The starting point is the same surrogate objective TRPO uses. For each time step in a batch, you take the probability the new policy assigns to the action that was actually taken, divide by the probability the old policy assigned to it, and multiply by the advantage, which is an estimate of how much better that action was than average. If the new policy equals the old one, this ratio is exactly one everywhere. Maximizing this objective without any constraint would push the ratio far from one and produce an excessively large update.

The clipped objective modifies this in two steps. First, clip the probability ratio to a narrow window around one. The paper uses a window of plus or minus twenty percent. Second, take the minimum of the clipped and the unclipped term. The minimum matters. When the advantage is positive, meaning the action was good, the policy would like to increase the ratio. Once the ratio exceeds the upper edge of the window, the clipped term is flat, so there is no gradient and no further incentive to increase it. When the advantage is negative, the policy would like to decrease the ratio, and the same thing happens at the lower edge. But the minimum also means that a change which makes the objective worse is never hidden by the clip. The clip only removes the incentive for movement that would improve the objective, never movement that would hurt it. So the whole thing is a pessimistic estimate, a lower bound on the unclipped surrogate. Near the old policy, the two agree exactly. Far from it, the clipped version is penalized.

The authors show a plot along the line between the old and updated policy parameters. The unclipped objective keeps rising as you move away, the KL divergence grows, and the clipped objective rises, peaks at a small divergence, then falls. So the clipped objective naturally stops the update at a sensible distance, without any explicit measurement of distance.

Because this is just a different loss function, it slots into a standard policy gradient implementation with automatic differentiation. You construct the clipped loss instead of the usual log probability times advantage, and you run multiple epochs of stochastic gradient ascent on it. That is the whole algorithmic change.

The full training loop is actor critic style. A number of parallel actors each run the current policy for a fixed number of time steps, in the paper's continuous control experiments two thousand and forty eight steps. Advantages are computed with a truncated form of generalized advantage estimation, which blends observed rewards over the segment with a learned value function to trade off bias and variance. Then the surrogate loss is optimized over all the collected data with minibatch Adam for several epochs, ten in the continuous control experiments and three on Atari. Then the old policy is replaced by the new one and the cycle repeats.

When the policy and value networks share parameters, the loss combines three terms. The clipped policy surrogate, a squared error term for the value function, and an entropy bonus that keeps the policy from collapsing too early and encourages exploration. Both extra terms are standard from earlier work. In the continuous control experiments the networks are not shared and there is no entropy bonus. On Atari both are used.

The adaptive KL variant replaces clipping with a penalty on the divergence between old and new policy. After each update it measures the actual divergence. If it came out much smaller than the target, the penalty coefficient is halved. If much larger, it is doubled. The multipliers are heuristic but the authors say the method is not sensitive to them, and the initial coefficient barely matters because it adjusts within a few updates.

## Experiments

There are four sets of experiments. The first is an ablation over surrogate objectives on a cheap benchmark: seven MuJoCo continuous control tasks from OpenAI Gym, namely half cheetah, hopper, inverted pendulum, inverted double pendulum, reacher, swimmer, and walker, each trained for one million time steps with three random seeds. The policy is a small fully connected network with two hidden layers of sixty four units, outputting a Gaussian over actions. The variants compared are no clipping or penalty, clipping with three window sizes, adaptive KL with three targets, and fixed KL with four coefficients. Scores are normalized per environment so that a random policy scores zero and the best result scores one, then averaged.

The second experiment compares clipped PPO against tuned implementations of TRPO, cross entropy method, vanilla policy gradient with adaptive step size, A2C, and A2C with a trust region, on the same seven MuJoCo tasks for one million steps.

The third is a showcase rather than a comparison. PPO is trained on three Roboschool humanoid tasks: running forward, running toward a target that moves, and the same while being pelted with cubes and having to get up. These run for fifty to one hundred million time steps with up to one hundred and twenty eight parallel actors, and no other algorithm is shown.

The fourth is Atari. PPO is compared against well tuned A2C and ACER on forty nine games from the Arcade Learning Environment, with the same network architecture for all three, and forty million game frames per run, three seeds.

What is not tested. Every continuous control experiment uses low dimensional state observations, not pixels. Nothing is on real robots. The MuJoCo comparison uses one million steps, which is short by later standards. There are no experiments on discrete action problems other than Atari, no partially observed tasks, no recurrent policies, no multi-agent settings, and no evaluation of robustness to hyperparameter changes beyond the clipping window and KL target.

## Results

In the ablation, clipping with a twenty percent window scored best, at about zero point eight on the normalized scale. Removing clipping and penalty entirely gave a negative score, because on half cheetah it produced policies worse than random. Adaptive and fixed KL penalties landed between zero point six and zero point seven five, so clearly better than nothing but clearly worse than clipping.

Against other algorithms on MuJoCo, PPO with clipping wins on almost all seven tasks, and where it does not win it is close. Against A2C on Atari it wins the large majority of games on both metrics. Against ACER, PPO wins more games when you score by average reward over the whole of training, which rewards fast learning, but ACER wins more games when you score by final performance. So PPO learns faster and ACER ends higher, and PPO is much simpler.

## Conclusion and downsides

The authors' claim is modest and holds up well. PPO gets the stability and reliability of trust region methods with a change of a few lines to a vanilla policy gradient implementation, it works with shared architectures where TRPO does not, and it performs better overall than the methods it is compared against. History has largely agreed. PPO became the default on-policy algorithm for years, including for training large language models with human feedback.

But the paper is thin on explanation, and several things are worth knowing before you rely on it.

First, the theoretical story is weaker than it sounds. The clipped objective is a lower bound on the surrogate, but the surrogate is only a local approximation of the true return, and nothing is proven about monotonic improvement in the way TRPO's theory is. The justification is essentially empirical.

Second, later work showed that the clipping does not actually constrain the policy. The ratio can end up far outside the window because gradient steps are taken on minibatches and the clip only zeros the gradient once the ratio is already outside. PPO's stability in practice depends heavily on implementation details the paper barely mentions: advantage normalization, value function clipping, orthogonal initialization, learning rate annealing, observation normalization. Reproductions without those details often perform much worse than reported.

Third, the paper does not explain why clipping beats the KL penalty, and gives no analysis of when it might not. It also spends a full section on the adaptive KL variant and then reports it as worse, which is honest but leaves the reader without guidance on when to prefer one.

Fourth, there is hyperparameter sensitivity that the experiments hide. The number of epochs, the minibatch size, and the clipping window interact. Too many epochs on the same batch still overfits and destabilizes training, clipping or not. The paper reports only one setting per domain.

Fifth, the evaluation is small by today's standards. Three seeds and one million steps on MuJoCo is noisy, and the baselines were tuned by the authors themselves. The Roboschool humanoid results have no comparison at all.

Finally, PPO is on-policy. Every batch is thrown away after a few epochs. It remains far less sample efficient than off-policy methods like soft actor critic on continuous control, which matters when environment interaction is expensive.

The open problems the paper leaves are exactly the ones the field then spent years on: understanding why PPO works, which implementation details are load bearing, and how to get trust region stability with off-policy data efficiency.

## Recap

The problem was that policy gradient methods either wasted data by taking one step per batch, or needed the complex second-order machinery of TRPO to take more. The approach is to change the objective rather than constrain the update. It works by clipping the ratio of new to old action probabilities to a narrow window and taking the pessimistic side, which removes any incentive to move the policy too far, so several epochs of ordinary gradient descent can safely be run on each batch. It beat TRPO and other on-policy methods on seven MuJoCo tasks and learned faster than A2C and ACER on Atari. The main downside is that its stability rests on empirical evidence and unstated implementation details rather than on the clipping mechanism itself. Read the full paper if you implement policy gradient methods, or if you want the ablation over objectives, which is the most informative table in it.
