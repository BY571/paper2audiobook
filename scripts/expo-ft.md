---
title: "EXPO-FT: Sample-Efficient Reinforcement Learning Finetuning for Vision-Language-Action Models"
authors: Perry Dong, Kuo-Han Hung, Tian Gao, Dorsa Sadigh, Chelsea Finn
year: 2026
source: https://arxiv.org/abs/2605.25477
---

## Opening

This is EXPO-FT, Sample-Efficient Reinforcement Learning Finetuning for Vision-Language-Action Models, by Perry Dong, Kuo-Han Hung, Tian Gao, Dorsa Sadigh and Chelsea Finn at Stanford, released as a preprint in 2026. It is a systems paper. It describes a complete recipe, with open-source code, for taking a pretrained generalist robot policy and fine-tuning it with reinforcement learning on a real robot until it succeeds every time, in about twenty minutes of robot interaction per task.

## The problem

Vision-language-action models, the large pretrained policies that take camera images and a text instruction and output robot motions, are impressively general. Given a new task they often succeed some of the time straight out of the box. But some of the time is not good enough to deploy. A robot that pockets the pool ball on three attempts out of four is a demo, not a product. Closing the gap from a reasonable success rate to a reliable one is the problem.

Reinforcement learning is the natural tool, because it improves a policy from its own successes and failures rather than from more demonstrations. But existing real-world reinforcement learning splits into two camps, and the authors argue neither fits. The first camp trains small policies from scratch, or trains a lightweight controller on top of a frozen model. Some of these systems are very sample efficient and reach near-perfect success in their own evaluations, but they cannot fine-tune the big model itself, so they throw away the semantic and behavioural knowledge that makes the pretrained policy general in the first place. The second camp does fine-tune the pretrained model, but either fails to reach a reliable success rate, needs a prohibitive number of environment interactions, or both.

There are also two technical obstacles specific to modern policies. Classical sample-efficient reinforcement learning, the off-policy actor-critic family, was designed around simple Gaussian policies, and modern robot models use diffusion or flow matching to produce actions, which do not fit that machinery directly. And modern models predict action chunks, sequences of several future actions per call, rather than single actions, while most reinforcement learning treats one action at a time.

## The idea in one breath

Take EXPO, a recently proposed reinforcement learning algorithm designed for expressive diffusion and flow policies, and build a full system around it for fine-tuning a vision-language-action model. Keep the big model as the base policy and fine-tune it directly, add a small learned edit policy that proposes corrections to the base model's actions, let a value function pick the best candidate, extend everything to operate on action chunks, and let a human operator step in with corrections during training when exploration alone is too slow. With those pieces, a pretrained policy goes from roughly sixty percent success to thirty out of thirty on every task tested, in an average of nineteen minutes of online robot data.

## Where it sits

The parent algorithm is EXPO, from the same first author, published at ICLR 2026. It exists because off-policy reinforcement learning with diffusion or flow policies is awkward: you cannot cheaply compute the probability of an action under such a policy, and you cannot backpropagate value gradients through a many-step sampling process without instability. EXPO's answer is to keep the expressive model as a base policy trained with its ordinary supervised loss, and to add a small Gaussian edit policy that learns to nudge the base model's proposals toward higher value. The value function is trained only on the actions actually chosen, so the updates stay grounded in near-optimal behaviour. This paper extends EXPO with action chunks and human interventions and wraps it in a real-robot pipeline.

The main points of comparison are three. HIL-SERL is the strongest real-world reinforcement learning system with human-in-the-loop corrections, and it reports near-perfect success on tasks like furniture assembly, but it trains a small policy from scratch and cannot use a pretrained model. DSRL is the state of the art for fine-tuning diffusion and flow policies with reinforcement learning; it keeps the model frozen and learns to steer the noise it samples from. HG-DAgger is the simplest option: keep imitating, with a human correcting the robot when it goes wrong, and no reward signal at all.

The distinguishing choices here are that the full pretrained model is updated inside the reinforcement learning loop rather than frozen or bypassed, that human corrections are folded into the same replay data as autonomous experience, and that the whole thing operates on action chunks rather than single steps.

## How it works

Start with the base policy. It is pi zero point five, a state-of-the-art generalist vision-language-action model from Physical Intelligence, initialised from a task-specific supervised checkpoint. Given the current observation, two camera images at low resolution plus the robot's own position and orientation, it produces a chunk of future actions. The authors have it draw eight different chunks per decision, because the model is stochastic and different samples are different plausible plans.

Next, the edit policy. This is a small network that takes the observation and one of those proposed chunks and outputs a bounded correction to add to it. The correction is scaled to be small, between five and twenty percent of the action range depending on the task, so an edited chunk is always a near neighbour of the base model's proposal. The edit policy is trained to maximise value with a mild entropy bonus, which is the ordinary actor update from soft actor-critic. Crucially, the value gradient flows into the edit policy only, never back through the base model's sampling process. That sidesteps the instability of differentiating through diffusion.

Then the critic. It is an ensemble of ten value networks that score an observation and a chunk of executed actions. For each target value, two networks are drawn at random and their minimum is used, to keep estimates conservative. The critic gets its own lightweight image encoder, a small residual network trained from scratch, rather than sharing the big model's vision backbone. The authors tried sharing and found it too expensive for the tight update loop, while the separate encoder loses nothing on task performance. The edit policy borrows the critic's visual features rather than having its own encoder; an ablation shows all three choices reach full success but sharing the critic's features converges fastest.

Now the decision rule. At each decision point there are sixteen candidate chunks: the eight base proposals and their eight edited versions. The critic scores all sixteen and the robot executes the one with the highest value. It is a hard argmax, not a sample. The same rule generates the target for the critic's own update: the value of the next state is the value of the best candidate there. That is the on-the-fly policy from EXPO, extended to chunks.

Chunks change one more thing. The model predicts a longer horizon, but only the first several actions are executed before replanning, eight in most tasks and four in the two that need the tightest feedback. The critic scores exactly the executed portion, and the discount is applied per chunk rather than per step. An ablation confirms replanning every four or eight steps works and every sixteen does not, so closed-loop correction has to happen at least every second or so.

The base model itself is updated during reinforcement learning with its original supervised objective on the replay buffer, unchanged. The buffer holds the initial demonstrations, everything the robot did autonomously, and everything a human did during interventions. So the base model keeps imitating whatever is in the buffer, including the corrections, while the edit policy and critic learn from reward. Freezing the base model instead is tested in the appendix and does not reach full success in the same budget.

Human interventions are the last ingredient. An operator watches and, with a small six-axis input device, can take over the robot at any moment for any number of steps. The human's actions replace the policy's for those steps, the rest of the chunk continues as planned, and the whole executed sequence goes into the replay buffer like any other. Interventions are frequent early and taper to zero as the policy improves. An ablation with no interventions at all, and one with half as many, both still reach thirty out of thirty but take substantially longer, so the human is an accelerator rather than a requirement.

Finally, the plumbing, which is much of the paper's contribution. Training and inference for a multi-billion-parameter model are slow, so the system is split into a learner process that owns the model and the replay buffer, and an actor process that talks to the robot, runs the policy, collects interventions, and ships transitions back. They can run synchronously or asynchronously; with two or fewer GPUs, synchronous is faster. Updates can happen every step, every episode, or every batch of episodes. The rewards are sparse and binary, produced by rule-based detectors on the camera images: for the candy scoop, check that candies are visible in the raised spoon, then check that the count in the source bin dropped. These detectors are over ninety-five percent accurate and take no reward engineering beyond a few pixel thresholds.

## Experiments

Everything is on one real robot arm with a wrist camera and a fixed side camera, commanded in end-effector velocity at ten hertz, trained on two H200 GPUs for eight to twenty thousand environment steps per task. Each task starts from ten to forty human teleoperation demonstrations and a supervised fine-tune to roughly forty percent success or better, then online training begins.

There are eight tasks, chosen to span precision, dynamics and variety. Flipping a fake fried egg in a pan with a spatula, which is contact-rich and dynamic. Routing string lights in three stages, hanging two bulbs on nails and plugging the cable in to light them up, each stage its own task. Scooping candies from one container to another. Picking a cube with the cube placed anywhere on the workspace. Inserting a flower stem into a wine bottle. And striking a cue ball to pocket a black ball, which needs precise speed control. Initial states are randomised, more widely than in the prior work being compared against, and this matters for the results.

The comparison methods are supervised fine-tuning alone, HG-DAgger, DSRL, and HIL-SERL, the last two only on four of the eight tasks, with HIL-SERL also given extra data on two tasks where it could not even start learning. Every method is scored on thirty evaluation trials judged by a human.

What is not tested. One robot, one base model, one lab. No simulation and no second embodiment. Every task is single-arm tabletop manipulation with a fixed camera setup; there are no mobile, bimanual or long-horizon multi-object tasks. The rewards are hand-written detectors, so the recipe has not been shown with learned reward models. Resets are manual for most tasks, which the authors name as their main limitation. DSRL and HIL-SERL are compared on only half the tasks, and the authors reimplemented those baselines themselves. Evaluation is thirty trials per method per task with no repeated seeds, and the n-step return length, which the ablation says matters, was not tuned.

## Results

The headline is thirty out of thirty on all eight tasks, from supervised starting points that averaged about twenty out of thirty, with an average of nineteen minutes of online data, ranging from fourteen minutes for cube pick and flower insert to thirty-five for the second string-light stage. HG-DAgger, the imitation-with-corrections baseline, averages about twenty-two out of thirty and is worst on the two dynamic or precise tasks, egg flip and pool shot, where it stays below twenty. DSRL, steering a frozen model, averages nineteen out of thirty on the four tasks it was run on. HIL-SERL from scratch averages about five and a half out of thirty on those four, and even with extra data manages twenty-seven on cube pick and thirteen on pool shot. The authors attribute HIL-SERL's collapse to the wide initial state randomisation, which a small policy trained from scratch cannot generalise across.

The training curves show EXPO-FT's success rate climbing steadily to one while the intervention rate falls to zero, and episode times shrinking as the policy gets more decisive. The prior methods mostly oscillate without converging in the same budget.

## Conclusion and downsides

The paper does what it sets out to do. It shows that a multi-billion-parameter generalist policy can be fine-tuned with off-policy reinforcement learning on a real robot, reliably and quickly, and it says which design choices carry the weight: updating the base model rather than freezing it, chunk-level values with frequent replanning, a separate cheap encoder for the critic, and human corrections as an accelerator. The ablations in the appendix are more informative than the main comparison, and the code release is a genuine contribution given how much of this is plumbing.

Now the caveats.

First, the comparison is tilted in ways the authors partly acknowledge. HIL-SERL was designed for a narrower initial state distribution and is being run outside its design envelope; its poor numbers say more about the setting than the algorithm. DSRL is run frozen, which is how it was proposed, but the appendix shows that freezing hurts this method too, so some of the gap is the freezing rather than the algorithm. And the baselines were reimplemented by the authors with hyperparameters chosen by the authors.

Second, thirty out of thirty is a ceiling, not a measurement. Every task saturates, so the results cannot distinguish a method that is barely reliable from one that is robust with margin. The more informative number is minutes to reliability, and that is only reported for the proposed method.

Third, nineteen minutes of robot data is not nineteen minutes of effort. Each task needs demonstrations, a supervised fine-tune to about forty percent, a hand-written reward detector, a reset procedure, and a human operator present throughout training. The wall-clock cost of the full pipeline is not reported.

Fourth, the ablation on pretraining is the most surprising result and the least explored. The system reaches full success even from a randomly initialised base model, just more slowly. That is good news for the algorithm but it undercuts part of the motivation, which was that the pretrained prior is what makes this work. It also raises the question of how much of the gain is the pretrained policy versus the human corrections versus the value-based selection, and the ablations answer this only on two tasks.

Fifth, the scale is one arm on a tabletop. The authors flag that manual resets and the compute cost of a billion-parameter model in a tight training loop are both open problems. Neither is solved here.

Finally, the sixteen-candidate argmax makes the executed policy deterministic and greedy with respect to a learned critic. That is the source of the reliability, and it is also a source of brittleness if the critic is wrong in a state it has not seen. Nothing in the paper tests robustness to distribution shift after training.

The open problems the authors name are automating resets and reducing the compute of training large models at control frequency. The one they do not name, but which the pretraining ablation points at, is understanding which part of the pipeline actually buys the sample efficiency.

## Recap

The problem was that pretrained generalist robot policies succeed often but not reliably, and existing reinforcement learning either cannot fine-tune such large models or needs too much robot time to do it. The approach is a full system around the EXPO algorithm: keep the big model as a base policy and keep training it, add a small edit policy that proposes corrections, and let a conservative value ensemble choose the best of sixteen candidate action chunks at every step. It works through chunk-level values with replanning every four to eight steps, a cheap separate vision encoder for the critic, sparse rule-based rewards, a learner and actor split across processes, and a human who corrects the robot early in training and then steps back. On eight real manipulation tasks it reaches thirty out of thirty in an average of nineteen minutes of online data, where imitation with corrections stays around twenty-two and reinforcement learning from scratch collapses under wide initial-state randomisation. The main downsides are that the baselines are run outside their design conditions, every result saturates so margins are invisible, the pipeline's full human and engineering cost is not counted, and the appendix shows the pretrained prior is not actually necessary. Read the full paper if you fine-tune robot policies with reinforcement learning; the appendix ablations and the hyperparameter tables are the useful parts, and the code is public.
