---
title: Real-Time Execution of Action Chunking Flow Policies
authors: Kevin Black, Manuel Y. Galliker, Sergey Levine
year: 2025
source: https://arxiv.org/abs/2506.07339
---

## Opening

This is Real-Time Execution of Action Chunking Flow Policies, by Kevin Black, Manuel Galliker and Sergey Levine at Physical Intelligence and UC Berkeley, published at NeurIPS 2025. It is a methods paper about robot control. It introduces an inference-time algorithm called real-time chunking, or RTC, which lets a large, slow robot policy keep moving smoothly while it thinks about what to do next.

## The problem

Modern robot policies are big. Vision-language-action models, the robot equivalent of large language models, take an image and a text instruction and produce motor commands, and they have billions of parameters. That makes them slow. The authors' own three-billion-parameter model spends about forty-six milliseconds just filling its attention cache on a top consumer GPU, before it has generated a single action. Run it over a network to a robot and you add tens of milliseconds more. Meanwhile the robot needs a new command every twenty milliseconds. So there is no way to run the model once per control step. The world does not pause while the model thinks.

The standard workaround is action chunking. Instead of one action per call, the policy predicts a whole chunk of future actions, say fifty of them, and the robot plays them back while the next chunk is computed. This helps, but it leaves two problems. First, most systems run synchronously: they execute a chunk, then stop and wait while the next one is generated. That produces visible pauses at every chunk boundary, which slows the task down and also changes the robot's dynamics in a way the training data never contained. Second, if you try to remove the pauses by generating the next chunk in the background while the current one plays, you hit a discontinuity problem. The policy's output is multimodal. Given a cup on the table, it may plan to go around it on the left or on the right, and both are valid. If the current chunk went left and the new chunk goes right, switching between them mid-motion produces a jerk that is unlike anything in the training data, and the robot's behaviour degrades from there.

The obvious smoothing fix, temporal ensembling, averages the overlapping predictions from several chunks. But the average of going left and going right is going through the cup. Averaging valid actions does not give a valid action.

## The idea in one breath

Treat the hand-over between chunks as an inpainting problem, the same problem an image model solves when it fills in a missing region of a photo. By the time a new chunk is ready, the first few actions of it have already been executed from the old chunk, so those are fixed. Freeze them, and ask the flow model to generate a new chunk that is consistent with that frozen prefix, using a guidance technique borrowed from image inpainting. Because the new chunk continues the old one rather than restarting, the strategy stays the same and the motion stays smooth. Nothing is retrained. It works on any diffusion or flow-based policy at inference time.

## Where it sits

The obvious alternative is to make the model faster: distill the diffusion process into one step, decode actions in parallel, quantise the weights. The authors' point is that none of these get inference below the twenty-millisecond control period for a billion-parameter model, so some form of asynchrony is needed regardless. Another line of work splits the policy into a slow planning module and a fast action module. That is compatible with real-time chunking but needs its own architecture and training recipe.

The closest prior method is bidirectional decoding, which keeps continuity between chunks by sampling many candidate chunks and picking the one closest to the previous plan. It works, but it needs a batch of samples from a strong model plus a batch from a deliberately weakened one, which costs far more compute than a single guided generation.

Temporal ensembling, from the original action chunking paper, is the smoothing baseline. The authors argue, and then show, that it fails on multimodal tasks for the averaging reason just described.

Real-time chunking's distinguishing property is that it is purely an inference-time change. Take any existing diffusion or flow policy, plug in the new sampler, and run it asynchronously with no retraining and no architecture change.

## How it works

Start with what a flow policy does. It takes an observation, samples a chunk of random noise the shape of the action chunk, and then refines that noise over a handful of steps, five in the real-robot experiments, by following a learned velocity field. After the last step you have a chunk of actions. Each refinement step is one forward pass of the network.

Now the timing. Say a chunk holds fifty actions at fifty hertz, so one second of motion. The robot starts executing it. Some time later the system starts generating the next chunk, using a fresh observation. Generation takes a certain number of control steps, the inference delay, which is about six steps in the authors' setup and could be sixteen with extra network latency. During those steps the robot keeps executing actions from the old chunk. So when the new chunk arrives, its first several actions are already in the past. They correspond to old-chunk actions that were, in fact, executed.

That observation is the whole trick. Those first few actions are not a choice; they are history. So the algorithm freezes them to the values that actually ran, and generates the rest of the chunk conditioned on them. This is exactly image inpainting: known pixels around a hole, generate the hole to be consistent with them.

The inpainting method comes from recent work on training-free image inverses with flow models, itself based on a technique called pseudoinverse guidance. At every refinement step, the model has a current noisy chunk and can form a quick estimate of what the final clean chunk would look like. The guidance compares that estimate to the target, meaning the frozen actions, and computes how the noisy chunk should be nudged so that the estimate moves toward the target. That nudge is a gradient through the network, computed by backpropagation, and it is added to the velocity field before the refinement step. The strength of the nudge depends on the refinement step, and it blows up toward the start of the process, so the authors clip it. That clipping is their addition, and their ablation in the appendix shows that without it the generated chunks diverge when you only use five refinement steps, which is what control needs.

The second ingredient is what they call soft masking. Freezing only the handful of already-executed actions turned out to be too weak a signal, especially when the inference delay is small. The new chunk would still sometimes switch to a different strategy after the frozen prefix ended. So instead of a hard boundary, they use all of the overlapping actions from the previous chunk, not just the executed ones, with a weight that is one for the executed prefix, decays exponentially over the remainder of the overlap, and is zero for the part of the new chunk that reaches beyond the old one. The intuition is that the old chunk's later actions are still good evidence of what the policy intended, just increasingly uncertain the further out they are, so they should guide but not dictate. An ablation compares exponential decay to linear, none, and hard masking, and exponential wins, though linear is close.

The third piece is the runtime system. A controller thread asks for an action every twenty milliseconds and supplies the latest observation. A background inference thread loops: wait until enough of the current chunk has been executed, take the remaining part of that chunk as the guide, estimate the coming inference delay conservatively from a buffer of recent delays, run the guided generation, then swap the new chunk in the moment it is ready. The execution horizon, how many actions run before the next generation starts, adapts to the measured delay, with a minimum of twenty-five steps in the real experiments. Because the delay is estimated and the guide includes the whole overlap, the system tolerates the delay being different from one call to the next.

The cost is the backward pass at every refinement step. On their model each refinement step goes from about three milliseconds to about seven, so five steps add roughly twenty milliseconds, and the model's total inference goes from seventy-six to ninety-seven milliseconds. That is the price of the guidance, and the second paper in this pair is about removing it.

## Experiments

There are two settings. The first is a new simulated benchmark of twelve tasks in Kinetix, a two-dimensional physics simulator with force-based control, chosen because standard imitation benchmarks are quasi-static and can be solved with long open-loop chunks. These tasks involve throwing, catching and balancing, they have noise added to the actions so that closed-loop correction matters, and because control is force-based there is no such thing as holding position, so inference delay has to be handled. Expert policies were trained with reinforcement learning, a million transitions were collected from a mixture of six experts per task, and small flow policies with a chunk length of eight were trained by imitation. Inference delays from zero to four steps are simulated. Baselines are naive asynchronous execution, bidirectional decoding, temporal ensembling, and real-time chunking with hard instead of soft masking. Each point is two thousand and forty-eight trials with confidence intervals.

The second setting is real. A bimanual robot with two six-degree-of-freedom arms and parallel grippers, driven by the group's pi zero point five vision-language-action model, on six tasks: lighting a candle with a match, plugging in both ends of an ethernet cable, making a bed with a mobile base, folding a shirt, folding a batch of crumpled laundry, and loading dishes into a sink with a mobile base. Inference runs on a separate workstation over wired ethernet. Baselines are synchronous execution, which is the default in prior work, and two temporal ensembling variants. On top of the natural latency they inject an extra hundred and two hundred milliseconds to imitate a bigger model or a remote server. Each task and method gets ten trials, four hundred and eighty episodes in all, about twenty-eight hours of robot time, scored by how many substeps of the task were completed and when.

What is not tested. The real robots use position control, so the simulator's force-control setting and the real setting differ in kind. No legged locomotion is tested in the real world, only in simulation, and the authors flag this. Bidirectional decoding is not run on the real robot because it was slower and worse in simulation. The method is only defined for diffusion and flow policies; autoregressive token-based policies are out of scope. No sim-to-real transfer is claimed. Everything real is on one robot platform with one base model.

## Results

In simulation, temporal ensembling performs badly at every delay, even zero, which confirms that averaging is the wrong operation on multimodal actions. Real-time chunking is the most robust to delay, beating bidirectional decoding with the gap widening as delay grows, while using far less compute. Soft masking beats hard masking, most clearly at small delays. And with delay fixed, shorter execution horizons help real-time chunking monotonically, meaning it can actually exploit more frequent replanning rather than being hurt by it.

On the real robot, the headline metric is throughput, task progress per minute. Real-time chunking scores best at every injected latency and is flat as latency grows, while synchronous execution degrades linearly and both temporal ensembling variants cannot run at all with added latency, because the oscillations trigger the robot's protective stop. Removing the inference pauses from the clock, real-time chunking still completes tasks in fewer control steps, so it is not just faster, it makes fewer mistakes and retries less. On the candle task, the most precision-sensitive and the only one without retrying, the final score is clearly higher. The bottom line from the abstract is a roughly twenty percent faster robot with smoother motion than any competitor.

## Conclusion and downsides

The framing is the paper's real contribution. Seeing the chunk hand-over as inpainting, with the executed prefix as the known region, is clean, general, and needs no training. The soft masking and guidance clipping are the engineering that made it work with few refinement steps, and both are honestly ablated. The runtime algorithm is spelled out in full pseudocode, which is rarer than it should be.

Now the limitations, some stated and some not.

First, it is not free. Every refinement step needs a backward pass, which increased their model's inference time by about a quarter. That is an odd property for a method whose purpose is to cope with latency: it adds latency. The follow-up paper from the same group exists precisely to remove this overhead by moving the conditioning into training.

Second, the guidance is an approximation. It nudges the generation using a local linearisation of the network, and the authors themselves note, in the follow-up, that this linearisation struggles as the frozen prefix gets longer. So the method is best at moderate delays and its advantage may shrink for very slow models or very long network round-trips.

Third, the real-world evidence is ten trials per condition. The throughput differences are reported with error bars and the significant ones are called out, but ten trials on a robot is a small sample, and the per-task plots show the methods often reaching similar final scores with the difference being in speed and retries.

Fourth, the simulated benchmark is new and built by the authors, with the expert data generated by their own reinforcement learning agents. That is a legitimate way to get a dynamic benchmark, but it also means no one else has calibrated it yet.

Fifth, there is a hyperparameter surface the paper only partly explores: the guidance clipping value, the decay schedule of the soft mask, the delay buffer, the minimum execution horizon. The ablations cover the first two. The defaults transferred from simulation to the real robot, which is encouraging, but a new platform may need retuning.

Finally, the method only applies to diffusion and flow policies. The authors say so. Policies that emit discrete action tokens autoregressively need a different mechanism.

The open problems the paper points at are the cost of the guidance, extension to more dynamic settings such as legged robots in the real world, and the relationship to classical model-predictive control, which also warm-starts each plan from the previous one and which the authors explicitly leave for future work.

## Recap

The problem was that large robot policies take longer to think than the robot can wait, and both stopping between action chunks and switching chunks naively produce behaviour the policy never saw in training. The approach is to generate the next chunk in the background while the current one plays, and to make the new chunk consistent with the old one by treating the hand-over as inpainting. It works by freezing the actions that will already have been executed by the time the new chunk arrives, softly weighting the rest of the overlap, and steering the flow model's refinement steps with a clipped guidance gradient so the generated chunk matches them, all at inference time with no retraining. In simulation it is the most delay-robust method tested, and on six real bimanual tasks it is about twenty percent faster than synchronous execution and immune to two hundred milliseconds of added latency, where smoothing baselines trip the robot's safety stop. The main downside is that the guidance needs a backward pass per refinement step, adding about a quarter to inference time, and it weakens as delays grow. Read the full paper if you deploy diffusion or flow policies on real hardware; the runtime pseudocode and the latency tables in the appendix are the parts you will want.
