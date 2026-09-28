---
title: "EXPO: Stable Reinforcement Learning with Expressive Policies"
authors: Perry Dong, Qiyang Li, Dorsa Sadigh, Chelsea Finn
year: 2026
source: https://proceedings.iclr.cc/paper_files/paper/2026/file/d56a652ad743308b24b6c4d0e6411dd7-Paper-Conference.pdf
---

## Opening

This is EXPO, Stable Reinforcement Learning with Expressive Policies, by Perry Dong, Qiyang Li, Dorsa Sadigh and Chelsea Finn at Stanford and UC Berkeley, published at ICLR 2026. It is an algorithm paper. It proposes a way to run sample-efficient, off-policy reinforcement learning on top of diffusion and flow-matching policies, the expressive policy classes that modern imitation learning uses, without the training instability that has made that hard.

## The problem

Imitation learning on large datasets has produced impressive robot policies, and the best of them are expressive: instead of a Gaussian over actions, they use a diffusion or flow-matching model that generates an action by iteratively refining noise over many steps. That lets them capture multimodal behaviour, where several different actions are all reasonable. But imitation alone tends to plateau below the reliability you need in the real world. The natural fix is to fine-tune with reinforcement learning, so the policy improves from its own experience.

Here is the catch. The workhorse of sample-efficient reinforcement learning is the off-policy actor-critic: learn a value function, and push the policy toward actions the value function rates highly. For a Gaussian policy that push is a gradient of the value with respect to the action, backpropagated into the policy parameters. For a diffusion policy, the action is the output of a long chain of denoising steps, and backpropagating a value gradient through that chain is expensive and unstable. It gets worse as the chain gets longer. Prior work has tried to route around this by adding value-based losses at intermediate denoising steps, by distilling the diffusion process down to one or two steps, or by keeping the expressive policy frozen and learning something small on top. None of these was a clean answer for online fine-tuning.

So the question the paper asks is: how do you maximise value with an expressive policy, stably, and sample-efficiently, given a prior dataset or a pretrained policy to start from?

## The idea in one breath

Never optimise the expressive policy against the value function at all. Train it only with its stable imitation objective, on whatever is in the replay buffer. Then build the value-maximising policy on the fly, out of two cheap pieces: a small Gaussian edit policy that learns to nudge each sampled action toward higher value, and a selection step that draws several candidate actions, edits each one, and picks whichever of the base and edited actions the critic scores highest. That constructed policy is used both to act in the environment and to compute the critic's training target. The expressive model provides diversity and stays close to the data; the edit and the argmax provide improvement.

## Where it sits

The closest relative is IDQL, which also trains a diffusion policy by imitation and picks the highest-value sample at inference. The difference is that IDQL only does that when acting, not inside the critic's update, and it constrains the critic to the offline data. EXPO uses the value-maximising selection in the temporal-difference backup too, and the paper's ablation shows that is the single most important choice.

RLPD is the sample-efficiency benchmark in the setting of learning online with prior data. It uses a plain Gaussian policy and oversamples the offline data. It is fast, but it has to rediscover the good behaviours in the data through exploration rather than reading them off directly.

Methods like DIPO, QSM and DAC train diffusion policies with value gradients by supervising the denoising process. In the paper's experiments they are often unstable or fail to learn on the harder tasks. Cal-QL is the standard offline-to-online baseline with a Gaussian policy and a calibrated critic; it pretrains a value function, which EXPO deliberately does not.

Two other ideas EXPO borrows from and combines: sampling-based maximisation, where you choose the best of several proposals rather than differentiating, and residual policies, where a small learned correction is added to a fixed base. EXPO's distinguishing move is to keep fine-tuning the base policy itself, by imitation, while doing the value maximisation elsewhere.

## How it works

There are three learned components and one non-learned rule.

The base policy is the expressive model, a diffusion policy in the experiments, though the authors stress the method does not care which expressive class you use. It is trained with the ordinary denoising objective, first on the offline dataset if you are pretraining, and then continuously on minibatches from the replay buffer as new experience arrives. It is never asked to maximise value. That is the source of stability: its training signal is the same one that made it work in the first place.

The edit policy is a small Gaussian network. It takes the state and an action sampled from the base policy, and outputs a correction to add to that action. It is trained with the standard entropy-regularised actor loss from soft actor-critic: increase the critic's value of the corrected action, while keeping some randomness. Because the gradient flows only into this small network, and the base policy's sample is just an input, there is no backpropagation through the denoising chain. The correction is bounded by a scale factor that is a hyperparameter, tuned per task between five percent and seventy percent of the action range. A small scale keeps edits close to what the data supports; a large one lets the policy explore further when the dataset is narrow. The authors say plainly that this is the one hyperparameter you have to tune.

The critic is an ensemble of ten value networks, with the minimum over two randomly chosen members used as the target, a standard trick for keeping estimates conservative.

The rule that ties them together is the on-the-fly policy. To act in a state, draw several actions from the base policy, eight in the experiments. Edit each one. That gives sixteen candidates. Score all sixteen with the critic and execute the best. The same rule defines the critic's learning target: the value of the next state is the critic's estimate at the best candidate in that next state. So the critic is doing proper Q-learning, bootstrapping from a maximising policy, rather than the SARSA-like update you would get by bootstrapping from a random sample of the imitation policy. The ablation shows that difference is decisive: with the argmax only at action time and not in the backup, learning is far slower.

The intuition the paper offers is geometric. The base policy's samples land in the modes of the behaviour distribution. The edit policy shifts each sample uphill in value within its mode. The argmax across candidates then picks between modes. Together they can both refine and switch, without ever pushing the expressive model somewhere its training signal cannot follow.

There is one more variant for the case where the offline data is too thin for imitation to learn anything useful. In that regime you need more exploration, and the usual way to get it is an entropy bonus in the critic's target. But an expressive policy has no closed-form entropy. The authors define a soft sampling distribution over the edited candidates, a softmax over their values, which does have an entropy, and use that in the backup. This entropy version is what rescues the one task where the plain method struggles.

Everything runs at a high update-to-data ratio of twenty gradient steps per environment step, with replay initialised from the demonstrations. The algorithm fits in a dozen lines of pseudocode and the code is public.

## Experiments

Everything is in simulation, on twelve sparse-reward continuous control tasks from four suites. Antmaze from D4RL: a quadruped navigating medium and large mazes, two dataset variants each. Adroit from D4RL: a twenty-eight-degree-of-freedom hand spinning a pen, opening a door, and relocating a ball, with narrow datasets. Robomimic: a seven-degree-of-freedom arm lifting a block, moving a can, and inserting a square peg, with the lift dataset cut down to ten demonstrations and the can task using the harder mixed-quality data. And two MimicGen tasks, threading a needle and stacking a cube, with mostly generated demonstrations. Every task uses a binary reward. Each result is three seeds with the spread shown.

Two settings are tested. Online: no pretraining, the offline data just seeds the replay buffer, and EXPO's base policy learns from it as it goes. Offline-to-online: the base policy is pretrained by imitation on the offline data, then fine-tuned. In the second setting EXPO pretrains only the policy, never the critic, because the authors want the method to work from any pretrained model, most of which come without a value function. The Adroit tasks skip pretraining because the data is too narrow.

Baselines are RLPD, IDQL, DIPO, QSM, DAC and Cal-QL, each in the setting it was designed for. Ablations cover the argmax in the backup, the action edits, the number of samples, the edit scale, the size and quality of the offline dataset, and fine-tuning with the offline data discarded.

What is not tested. No real robot. No image observations; all twelve tasks use low-dimensional state. No action chunking; every action is a single step, and extending to chunks is not attempted. Only a diffusion base policy is instantiated, so the claim of being agnostic to policy class is asserted rather than demonstrated with a flow model. The baselines were run by the authors, and RLPD is run without pretraining in both settings. And nothing is said about wall-clock cost, though the discussion admits that sampling and editing many candidates for every element of every batch is expensive.

## Results

In the online setting, EXPO matches or beats the best baseline on almost every task, and the gap is often large. Against RLPD, which is the strong baseline here, EXPO is consistently more sample efficient except on the ball relocation task, where the data is too narrow for imitation to extract a useful starting behaviour. The diffusion-based baselines IDQL, DIPO and QSM frequently fail to learn at all on the harder tasks.

In the offline-to-online setting, the headline is that EXPO does not dip. Most methods lose performance when they switch from offline pretraining to online fine-tuning, and on the manipulation tasks every baseline except RLPD drops noticeably. EXPO starts near its pretrained performance and climbs, because the base policy stays anchored to the behaviour distribution while the edits and argmax improve within it. DAC pretrains well and then collapses online. IDQL barely improves after pretraining. Cal-QL is strong on the easier mazes and weak on the rest.

The ablations are the most informative part. Removing the argmax from the critic's backup roughly halves the learning speed on the two manipulation tasks tested. Removing the action edits stalls learning on the pen task, which needs exploration, and slows it on the square task, which does not. The quality of the offline data, measured by how well plain imitation does on it, predicts fine-tuning performance almost linearly for the base method, and the entropy variant flattens that curve so that even data on which imitation scores under ten percent leads to a near-perfect policy. And fine-tuning a pretrained policy with the offline data thrown away, using only warm-start rollouts, works about as well as keeping it, where Cal-QL followed by SAC fails outright. Averaged across tasks the authors summarise the gain as two to three times better sample efficiency than prior methods.

## Conclusion and downsides

The core design decision is a good one and it is well supported: get stability by never optimising the expressive policy against value, and get improvement by constructing the maximising policy out of samples, edits and a critic. The ablations isolate which piece matters most, and the no-dip behaviour in offline-to-online fine-tuning is the property practitioners actually care about. The paper is also honest about hyperparameter sensitivity and about compute.

The limitations, some stated and some not.

First, compute. Each critic update needs eight base samples and eight edits per element of the batch, and the base samples each require a full denoising chain of ten steps. With a batch of two hundred and fifty-six and twenty updates per environment step, that is a lot of diffusion sampling. The authors flag this and leave it for future work. For a small MLP policy on state inputs it is fine; for a billion-parameter model with images it is the central engineering problem, which is exactly what later work applying the method to real robots had to solve.

Second, the edit scale has to be tuned per task, and the appendix shows performance depends on it. The guidance given, small when the data is good and large when exploration is needed, is sensible but it means a new task needs a sweep.

Third, the method assumes a useful prior. The base policy is trained by imitation, so if the data does not contain the behaviour you want, the base samples are not in the right region and the bounded edits cannot get there. The relocation task shows this, and the entropy variant only partly fixes it. The authors state this assumption; it is worth remembering that it rules out learning genuinely new skills from scratch.

Fourth, the argmax over a learned critic makes the executed policy greedy and deterministic apart from the edit noise. That is what gives fast improvement, and it is also a standard recipe for exploiting critic errors. The ensemble minimum guards against this, but there is no analysis of what happens when the critic is wrong in a state the candidates have not visited.

Fifth, the evaluation is entirely simulated, on state observations, with single-step actions and one expressive policy class. Every generalisation beyond that, to images, chunks, flow models and hardware, was left to later work, and readers of this paper alone should not assume them.

The open problems the authors name are the sampling cost and the uninformed-prior case. The one they do not name is how the method interacts with action chunking, where the critic must score a sequence and the edit must be coherent across it; later work by the same authors that took the method onto real robots had to solve exactly that.

## Recap

The problem was that fine-tuning diffusion or flow policies with off-policy reinforcement learning is unstable, because pushing value gradients back through a long denoising chain does not work well. The approach is to leave the expressive policy alone, training it only by imitation on the replay buffer, and to build the value-maximising policy on the fly from cheap parts. It works by sampling several actions from the base policy, nudging each with a small learned edit policy trained against the critic, and executing whichever base or edited action the critic ranks highest, with that same argmax used inside the critic's own update. On twelve simulated sparse-reward tasks it is two to three times more sample efficient than prior methods and, unlike them, does not lose performance when switching from offline pretraining to online fine-tuning. The main downsides are the cost of sampling many candidates through a diffusion chain at every update, a per-task edit scale that must be tuned, and a dependence on the offline data already containing useful behaviour. Read the full paper if you want to fine-tune an expressive policy with reinforcement learning; the twelve-line algorithm box and the ablation section are what you need, and the code is public.
